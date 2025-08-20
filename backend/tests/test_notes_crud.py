from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

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

    async def fetchrow(self, sql: str, *params: Any) -> Optional[Dict[str, Any]]:
        s = sql.lower().strip()
        if s.startswith("insert into public.notes"):
            new_id = str(uuid4())
            row = _NoteRow(
                id=new_id,
                url=str(params[0]),
                title=str(params[1] or ""),
                description=str(params[2] or ""),
                tags=list(params[3] or []),
                created_at=_now(),
                updated_at=_now(),
            )
            self.store[new_id] = row
            return {
                "id": row.id,
                "url": row.url,
                "title": row.title,
                "description": row.description,
                "tags": row.tags,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        if s.startswith("update public.notes set"):
            note_id = str(params[-1])
            row = self.store.get(note_id)
            if not row:
                return None
            row.url = str(params[0])
            row.title = str(params[1])
            row.description = str(params[2])
            row.tags = list(params[3])
            row.updated_at = _now()
            return {
                "id": row.id,
                "url": row.url,
                "title": row.title,
                "description": row.description,
                "tags": row.tags,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        if s.startswith(
            "select id, url, title, description, tags, created_at, updated_at from public.notes where id ="
        ):
            note_id = str(params[0])
            row = self.store.get(note_id)
            if not row:
                return None
            return {
                "id": row.id,
                "url": row.url,
                "title": row.title,
                "description": row.description,
                "tags": row.tags,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        raise AssertionError(f"Unhandled fetchrow SQL: {sql}")

    async def fetch(self, sql: str, *params: Any) -> List[Dict[str, Any]]:
        s = sql.lower().strip()
        if s.startswith(
            "select id, url, title, description, tags, created_at, updated_at from public.notes"
        ):
            rows = list(self.store.values())
            idx = 0
            if "tags @>" in s and params:
                tag_list = list(params[idx])
                idx += 1
                rows = [r for r in rows if all(t in r.tags for t in tag_list)]
            if "|| ' ' ||" in s and "% $" in s and idx < len(params):
                q = str(params[idx]).lower()
                idx += 1
                rows = [r for r in rows if (q in (r.title + " " + r.description).lower())]
            limit = int(params[-2])
            offset = int(params[-1])
            rows_sorted = sorted(rows, key=lambda r: r.updated_at, reverse=True)
            rows_page = rows_sorted[offset : offset + limit]
            return [
                {
                    "id": r.id,
                    "url": r.url,
                    "title": r.title,
                    "description": r.description,
                    "tags": r.tags,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at,
                }
                for r in rows_page
            ]
        raise AssertionError(f"Unhandled fetch SQL: {sql}")

    async def execute(self, sql: str, *params: Any) -> str:
        s = sql.lower().strip()
        if s.startswith("delete from public.notes where id ="):
            note_id = str(params[0])
            if note_id in self.store:
                del self.store[note_id]
                return "DELETE 1"
            return "DELETE 0"
        raise AssertionError(f"Unhandled execute SQL: {sql}")


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


def test_notes_crud_and_scraper(monkeypatch):
    # Configure env to use mock embeddings and avoid real DB
    monkeypatch.setenv("SUPABASE_DB_URL", "postgresql://user:pass@localhost:5432/db?sslmode=require")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("EMBED_PROVIDER", "mock")

    # Reset settings cache
    from backend.settings import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]

    # Install fake DB pool
    store: Dict[str, _NoteRow] = {}
    from backend.db import db_pool

    db_pool._pool = FakePool(store)  # type: ignore[attr-defined]

    # Mock OG scraper to avoid network
    from backend.services import og_scraper

    class DummyMeta:
        def __init__(self) -> None:
            self.title = "Dummy Title"
            self.description = "Dummy Description"

    async def fake_scrape(url: str):
        return DummyMeta()

    monkeypatch.setattr(og_scraper, "fetch_og_metadata", fake_scrape)

    # Build app and run the scenario using httpx ASGI client
    from backend.main import app

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # Health
            r = await client.get("/api/health")
            assert r.status_code == 200 and r.json().get("ok") is True

            # Create
            create_body = {
                "url": "https://example.com/m4-test",
                "title": "M4 Test Title",
                "description": "Testing CRUD and trigram",
                "tags": ["m4test", "tagB"],
            }
            r = await client.post("/api/notes", json=create_body)
            assert r.status_code == 200
            note_id = r.json()["id"]

            # List with tag AND
            r = await client.get("/api/notes", params={"tags": "m4test,tagB", "limit": 50, "offset": 0})
            assert r.status_code == 200
            assert note_id in [n["id"] for n in r.json()]

            # List with q (substring fallback in fake)
            r = await client.get("/api/notes", params={"q": "trigram", "limit": 50, "offset": 0})
            assert r.status_code == 200
            assert note_id in [n["id"] for n in r.json()]

            # Update title and observe updated_at
            r_before = await client.get("/api/notes", params={"tags": "m4test,tagB", "limit": 1, "offset": 0})
            before = r_before.json()[0]
            r = await client.put(f"/api/notes/{note_id}", json={"title": "M4 Updated"})
            assert r.status_code == 200
            r_after = await client.get("/api/notes", params={"tags": "m4test,tagB", "limit": 1, "offset": 0})
            after = r_after.json()[0]
            assert before["updated_at"] != after["updated_at"]

            # Pagination sanity
            r1 = await client.get("/api/notes", params={"limit": 1, "offset": 0})
            r2 = await client.get("/api/notes", params={"limit": 1, "offset": 1})
            ids_p1 = [n["id"] for n in r1.json()]
            ids_p2 = [n["id"] for n in r2.json()]
            assert ids_p1 != ids_p2 or len(ids_p1) == 0

            # OG scraper endpoint (mocked)
            r = await client.get("/api/og-scrape", params={"url": "https://example.com"})
            assert r.status_code == 200
            assert r.json().get("title") == "Dummy Title"

            # Delete
            r = await client.delete(f"/api/notes/{note_id}")
            assert r.status_code == 200 and r.json().get("ok") is True

            # Validation 422 on bad URL
            r = await client.post("/api/notes", json={"url": "not-a-url"})
            assert r.status_code == 422

    asyncio.run(scenario())


