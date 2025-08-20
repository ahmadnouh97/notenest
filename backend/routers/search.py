from __future__ import annotations

import re
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from ..db import db_pool
from ..schemas import (
    ChatRequest,
    NoteOut,
    SearchRequest,
    SearchResultItem,
)
from ..services.embeddings import EmbeddingError, get_embedding
from ..services.chat_providers import ChatMessage, ChatProviderError, stream_chat_tokens
from ..settings import get_settings


router = APIRouter(prefix="/api", tags=["search", "chat"])


def _clean_text(value: Optional[str], *, max_len: int = 12000) -> str:
    if not value:
        return ""
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) > max_len:
        return text[:max_len]
    return text


def _vector_literal(vec: Sequence[float]) -> str:
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


@router.post("/search", response_model=List[SearchResultItem])
async def semantic_search(payload: SearchRequest) -> List[SearchResultItem]:
    settings = get_settings()
    query_text = _clean_text(payload.query)
    if not query_text:
        return []

    # Compute embedding with graceful fallback per settings
    provider = None
    api_key = None
    if not settings.hf_api_key and not settings.openai_api_key:
        provider = "mock"

    try:
        qvec = await get_embedding(query_text, provider=provider, api_key=api_key)
    except EmbeddingError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Fit vector to DB dimension and re-normalize
    target_dim = int(settings.embed_dimension or len(qvec))
    if len(qvec) != target_dim:
        if len(qvec) > target_dim:
            qvec = qvec[:target_dim]
        else:
            qvec = list(qvec) + [0.0] * (target_dim - len(qvec))
        # L2 re-normalize
        s = sum(v * v for v in qvec) or 1.0
        inv = (1.0 / (s ** 0.5))
        qvec = [v * inv for v in qvec]

    qvec_literal = _vector_literal(qvec)

    hybrid = 0.7 if payload.hybridWeight is None else float(payload.hybridWeight)
    hybrid = 0.0 if hybrid < 0 else (1.0 if hybrid > 1.0 else hybrid)
    top_k = int(payload.topK or 10)
    if top_k < 1:
        top_k = 1
    if top_k > 200:
        top_k = 200

    # Build dynamic SQL with optional tag filter and hybrid ranking
    conditions: List[str] = []
    params: List[Any] = []

    if payload.tags:
        conditions.append(f"tags @> ${len(params) + 1}::text[]")
        params.append(list(payload.tags))

    where_clause = f" where {' and '.join(conditions)}" if conditions else ""

    # vector_cosine_ops: distance smaller means more similar. Convert to similarity 1 - dist.
    # trigram similarity on combined text
    score_expr = (
        f"({hybrid:.6f}) * coalesce(1.0 - (embedding <=> ${len(params) + 1}::vector), 0.0) + "
        f"({1.0 - hybrid:.6f}) * similarity((coalesce(title,'') || ' ' || coalesce(description,'')), ${len(params) + 2})"
    )
    params.append(qvec_literal)
    params.append(query_text)

    sql = (
        "select id, url, title, description, tags, created_at, updated_at, "
        f"{score_expr} as score "
        "from public.notes"
        f"{where_clause} "
        f"order by score desc limit ${len(params) + 1}"
    )
    params.append(top_k)

    async with db_pool.pool.acquire() as conn:
        try:
            rows = await conn.fetch(sql, *params)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to search notes: {exc}")

    results: List[SearchResultItem] = []
    for r in rows:
        results.append(
            SearchResultItem(note=_row_to_note_out(r), score=float(r["score"]))
        )
    return results


def _build_citation_context(items: List[SearchResultItem]) -> Tuple[str, List[Dict[str, str]]]:
    citations: List[Dict[str, str]] = []
    parts: List[str] = []
    for idx, item in enumerate(items, start=1):
        n = item.note
        citations.append({"id": n.id, "title": n.title, "url": n.url})
        parts.append(f"[{idx}] {n.title}\n{n.description}\nSource: {n.url}")
    context = "\n\n".join(parts)
    return context, citations


@router.post("/chat")
async def rag_chat(payload: ChatRequest):
    settings = get_settings()

    # Extract the latest user message to embed
    user_messages = [m for m in payload.messages if (m.role or "").lower() == "user"]
    latest_user = user_messages[-1].content if user_messages else ""
    latest_user = _clean_text(latest_user)

    # Retrieve topK context using the same hybrid search
    search_req = SearchRequest(
        query=latest_user or "",
        tags=payload.tags,
        topK=payload.topK or 5,
        hybridWeight=0.7,
    )
    search_results = await semantic_search(search_req) if latest_user else []

    context_block, citations = _build_citation_context(search_results)

    # Construct messages with context and citation instructions
    system_prefix = (
        "You are a helpful assistant. Use the provided notes as context. "
        "Cite sources inline using [n] where n is the citation number. If the answer is unknown, say so."
    )
    context_instruction = (
        "Context notes (use them to answer and include citation numbers):\n" + context_block
        if context_block
        else "No context available. Answer from general knowledge."
    )

    chat_messages: List[ChatMessage] = [
        ChatMessage(role="system", content=system_prefix),
        ChatMessage(role="system", content=context_instruction),
    ]
    # Append user/assistant history
    for m in payload.messages:
        chat_messages.append(ChatMessage(role=m.role, content=m.content))

    provider = (payload.provider or "groq").lower()
    model = payload.model or "openai/gpt-oss-120b"
    # Use server environment API keys (no longer accept client-supplied keys)
    api_key = None
    if provider == "groq" and settings.groq_api_key:
        api_key = settings.groq_api_key
    elif provider == "openai" and settings.openai_api_key:
        api_key = settings.openai_api_key
    elif provider == "openrouter" and settings.openrouter_api_key:
        api_key = settings.openrouter_api_key

    async def event_generator() -> AsyncIterator[Dict[str, str] | str]:
        try:
            async for token in stream_chat_tokens(
                provider=provider, model=model, messages=chat_messages, api_key=api_key
            ):
                # Stream raw tokens
                yield token
        except ChatProviderError as exc:
            # Surface provider errors to the client as an SSE error event
            yield {"event": "error", "data": str(exc)}
            return
        # Final event with citations metadata
        import json as _json

        yield {
            "event": "done",
            "data": _json.dumps({"citations": citations}),
        }

    return EventSourceResponse(event_generator())


