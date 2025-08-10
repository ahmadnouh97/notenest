from __future__ import annotations

import re
from typing import Any, List, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException, Query

from ..db import db_pool
from ..schemas import NoteCreate, NoteOut, NoteUpdate
from ..services.embeddings import EmbeddingError, get_embedding
from ..settings import get_settings
from ..services.og_scraper import fetch_og_metadata


router = APIRouter(prefix="/api/notes", tags=["notes"])


def _clean_text(value: Optional[str], *, max_len: int = 4000) -> str:
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) > max_len:
        return text[:max_len]
    return text


def _vector_literal(vec: Sequence[float]) -> str:
    # pgvector accepts a bracketed, comma-separated list
    return "[" + ",".join(f"{float(x):.7f}" for x in vec) + "]"


def _row_to_note_out(row: Any) -> NoteOut:
    return NoteOut(
        id=str(row["id"]),
        url=row["url"],
        title=row["title"],
        description=row["description"],
        tags=list(row["tags"] or []),
        created_at=row["created_at"].isoformat(),
        updated_at=row["updated_at"].isoformat(),
    )


@router.post("", response_model=NoteOut)
async def create_note(payload: NoteCreate) -> NoteOut:
    settings = get_settings()
    url = str(payload.url)

    title = _clean_text(payload.title)
    description = _clean_text(payload.description, max_len=8000)
    tags = payload.tags

    # Fill missing metadata via OG scraping
    if not title or not description:
        try:
            scraped = await fetch_og_metadata(url)
            if not title:
                title = _clean_text(scraped.title)
            if not description:
                description = _clean_text(scraped.description, max_len=8000)
        except Exception:
            # Non-fatal: proceed with provided fields
            pass

    # Ensure we have something to embed
    base_text = _clean_text(f"{title}\n\n{description}", max_len=12000)

    # Choose embedding strategy
    provider = None
    api_key = None
    if not settings.hf_api_key:
        # Fallback to mock embeddings for local/dev if HF key is missing
        provider = "mock"

    try:
        vector = await get_embedding(base_text, provider=provider, api_key=api_key)
    except EmbeddingError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Fit vector to DB dimension and re-normalize
    target_dim = int(settings.embed_dimension or len(vector))
    if len(vector) != target_dim:
        if len(vector) > target_dim:
            vector = vector[:target_dim]
        else:
            vector = list(vector) + [0.0] * (target_dim - len(vector))
        # L2 re-normalize
        s = sum(v * v for v in vector) or 1.0
        inv = (1.0 / (s ** 0.5))
        vector = [v * inv for v in vector]

    vector_literal = _vector_literal(vector)

    sql = (
        "insert into public.notes (url, title, description, tags, embedding) "
        "values ($1, $2, $3, $4::text[], $5::vector) "
        "returning id, url, title, description, tags, created_at, updated_at"
    )
    async with db_pool.pool.acquire() as conn:
        try:
            row = await conn.fetchrow(sql, url, title or "", description or "", tags, vector_literal)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to insert note: {exc}")

    return _row_to_note_out(row)


@router.get("", response_model=List[NoteOut])
async def list_notes(
    tags: Optional[str] = Query(default=None, description="Comma-separated list of tags (AND semantics)"),
    q: Optional[str] = Query(default=None, description="Keyword to search via trigram similarity"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> List[NoteOut]:
    conditions: List[str] = []
    params: List[Any] = []

    # Tag filter (AND): tags @> '{...}'
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        if tag_list:
            conditions.append(f"tags @> ${len(params) + 1}::text[]")
            params.append(tag_list)

    # Trigram keyword search on combined title+description
    order_by = "updated_at desc"
    if q:
        conditions.append(
            f"(coalesce(title,'' ) || ' ' || coalesce(description,'')) % ${len(params) + 1}"
        )
        params.append(q)
        order_by = (
            f"similarity((coalesce(title,'' ) || ' ' || coalesce(description,'')), ${len(params)}) desc, updated_at desc"
        )

    where_clause = f" where {' and '.join(conditions)}" if conditions else ""
    sql = (
        "select id, url, title, description, tags, created_at, updated_at "
        "from public.notes"
        f"{where_clause} "
        f"order by {order_by} "
        f"limit ${len(params) + 1} offset ${len(params) + 2}"
    )
    params.extend([limit, offset])

    async with db_pool.pool.acquire() as conn:
        try:
            rows = await conn.fetch(sql, *params)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to list notes: {exc}")

    return [_row_to_note_out(r) for r in rows]


@router.put("/{note_id}", response_model=NoteOut)
async def update_note(note_id: str, payload: NoteUpdate) -> NoteOut:
    # Fetch current row
    async with db_pool.pool.acquire() as conn:
        current = await conn.fetchrow(
            "select id, url, title, description, tags, created_at, updated_at from public.notes where id = $1",
            note_id,
        )
        if current is None:
            raise HTTPException(status_code=404, detail="Note not found")

        new_url = str(payload.url) if payload.url is not None else current["url"]
        new_title = _clean_text(payload.title) if payload.title is not None else current["title"]
        new_description = (
            _clean_text(payload.description, max_len=8000)
            if payload.description is not None
            else current["description"]
        )
        new_tags = payload.tags if payload.tags is not None else list(current["tags"] or [])

        # Determine if embedding must be recomputed
        needs_reembed = (new_title != current["title"]) or (new_description != current["description"])
        vector_literal: Optional[str] = None
        if needs_reembed:
            settings = get_settings()
            base_text = _clean_text(f"{new_title}\n\n{new_description}", max_len=12000)
            provider = None
            api_key = None
            if not settings.hf_api_key:
                provider = "mock"
            try:
                vector = await get_embedding(base_text, provider=provider, api_key=api_key)
            except EmbeddingError as exc:
                raise HTTPException(status_code=502, detail=str(exc))
            # Fit to DB dimension and re-normalize
            target_dim = int(settings.embed_dimension or len(vector))
            if len(vector) != target_dim:
                if len(vector) > target_dim:
                    vector = vector[:target_dim]
                else:
                    vector = list(vector) + [0.0] * (target_dim - len(vector))
                s = sum(v * v for v in vector) or 1.0
                inv = (1.0 / (s ** 0.5))
                vector = [v * inv for v in vector]
            vector_literal = _vector_literal(vector)

        # Build dynamic update statement
        fields: List[str] = []
        params: List[Any] = []

        fields.append(f"url = ${len(params) + 1}")
        params.append(new_url)
        fields.append(f"title = ${len(params) + 1}")
        params.append(new_title)
        fields.append(f"description = ${len(params) + 1}")
        params.append(new_description)
        fields.append(f"tags = ${len(params) + 1}::text[]")
        params.append(new_tags)
        if vector_literal is not None:
            fields.append(f"embedding = ${len(params) + 1}::vector")
            params.append(vector_literal)

        sql = (
            "update public.notes set "
            + ", ".join(fields)
            + f" where id = ${len(params) + 1} returning id, url, title, description, tags, created_at, updated_at"
        )
        params.append(note_id)

        try:
            row = await conn.fetchrow(sql, *params)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to update note: {exc}")

    if row is None:
        raise HTTPException(status_code=404, detail="Note not found")

    return _row_to_note_out(row)


@router.delete("/{note_id}")
async def delete_note(note_id: str) -> dict:
    async with db_pool.pool.acquire() as conn:
        try:
            result = await conn.execute("delete from public.notes where id = $1", note_id)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to delete note: {exc}")

    # asyncpg returns a status string like "DELETE 1"
    if not result.startswith("DELETE"):
        raise HTTPException(status_code=500, detail="Unexpected delete result")

    return {"ok": True}


