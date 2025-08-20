from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _NoteRow:
    id: str
    url: str
    title: str
    description: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class FakeConnection:
    def __init__(self, store: Dict[str, _NoteRow]) -> None:
        self.store = store

    async def fetch(self, sql: str, *params: Any) -> List[Dict[str, Any]]:
        s = sql.lower().strip()
        if (
            s.startswith(
                "select id, url, title, description, tags, created_at, updated_at,"
            )
            and "order by score desc" in s
        ):
            # Semantic search emulation
            rows = list(self.store.values())
            idx = 0
            # Optional tags AND filter
            if "tags @>" in s and params:
                tag_list = list(params[idx])
                idx += 1
                rows = [r for r in rows if all(t in r.tags for t in tag_list)]
            # Next params: qvec_literal (ignored) and query_text
            if idx < len(params):
                # skip vector literal
                idx += 1
            q = str(params[idx]) if idx < len(params) else ""
            idx += 1
            # Last param is limit
            top_k = int(params[idx]) if idx < len(params) else 10

            def _score(note: _NoteRow) -> float:
                text = (note.title + " " + note.description).lower()
                return 1.0 if q.lower() in text else 0.0

            rows_sorted = sorted(rows, key=_score, reverse=True)
            rows_page = rows_sorted[:top_k]
            return [
                {
                    "id": r.id,
                    "url": r.url,
                    "title": r.title,
                    "description": r.description,
                    "tags": r.tags,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                    "score": _score(r),
                }
                for r in rows_page
            ]
        raise AssertionError(f"Unhandled fetch SQL: {sql}")


class FakeAcquire:
    def __init__(self, store: Dict[str, _NoteRow]) -> None:
        self.store = store

    async def __aenter__(self) -> FakeConnection:  # type: ignore[override]
        return FakeConnection(self.store)

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        return None


class FakePool:
    def __init__(self, store: Dict[str, _NoteRow]) -> None:
        self.store = store

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self.store)


def setup_module(module):  # noqa: D401
    import os

    os.environ.setdefault(
        "SUPABASE_DB_URL", "postgresql://user:pass@localhost:5432/db?sslmode=require"
    )
    os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
    # Force deterministic, offline embeddings
    os.environ.setdefault("EMBED_PROVIDER", "mock")


async def _build_app_with_store() -> tuple[httpx.AsyncClient, Dict[str, _NoteRow]]:
    # Reset settings cache to pick up test env
    from backend.settings import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]

    # Install fake DB pool with seeded notes
    store: Dict[str, _NoteRow] = {}

    n1 = _NoteRow(
        id="11111111-1111-1111-1111-111111111111",
        url="https://example.com/one",
        title="Note One",
        description="This is the first note about vectors and search",
        tags=["tagA", "tagB"],
        created_at=_now(),
        updated_at=_now(),
    )
    n2 = _NoteRow(
        id="22222222-2222-2222-2222-222222222222",
        url="https://example.com/two",
        title="Another Entry",
        description="Completely unrelated content",
        tags=["tagB"],
        created_at=_now(),
        updated_at=_now(),
    )
    store[n1.id] = n1
    store[n2.id] = n2

    from backend.db import db_pool

    db_pool._pool = FakePool(store)  # type: ignore[attr-defined]

    from backend.main import app

    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://test")
    return client, store


def run(coro):
    # Use asyncio.run to create a fresh event loop per test invocation.
    return asyncio.run(coro)


def test_search_endpoint_basic():
    async def scenario():
        client, _store = await _build_app_with_store()
        async with client:
            # Basic search by keyword
            r = await client.post(
                "/api/search",
                json={"query": "note", "topK": 5},
            )
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data, list)
            # Expect the first item to be Note One with higher score
            assert len(data) >= 1
            assert data[0]["note"]["title"] == "Note One"

            # Tag filtered search should return only tagA/tagB note
            r2 = await client.post(
                "/api/search",
                json={"query": "note", "tags": ["tagA", "tagB"], "topK": 5},
            )
            assert r2.status_code == 200
            data2 = r2.json()
            assert len(data2) == 1
            assert data2[0]["note"]["title"] == "Note One"

    run(scenario())


def test_chat_sse_stream_and_citations():
    async def scenario():
        client, _store = await _build_app_with_store()
        async with client:
            body = {
                "messages": [{"role": "user", "content": "Tell me about Note One"}],
                "topK": 3,
                "provider": "mock",
                "model": "dummy",
            }
            async with client.stream("POST", "/api/chat", json=body) as resp:
                assert resp.status_code == 200
                assert resp.headers.get("content-type", "").startswith("text/event-stream")

                tokens: List[str] = []
                done_payload: Optional[str] = None
                pending_done = False
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("event:") and "done" in line:
                        pending_done = True
                        continue
                    if line.startswith("data:"):
                        data = line[len("data:") :]
                        if data.startswith(" "):
                            # Remove only the protocol's single space after colon
                            data = data[1:]
                        if pending_done:
                            done_payload = data
                            break
                        tokens.append(data)

                assert "".join(tokens) == "Hello world!"
                import json as _json

                assert done_payload is not None
                meta = _json.loads(done_payload)
                cits = meta.get("citations") or []
                assert isinstance(cits, list) and len(cits) >= 1
                assert cits[0]["title"] == "Note One"

    run(scenario())


