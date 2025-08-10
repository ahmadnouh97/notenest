from __future__ import annotations

import math
import os
import asyncio


def _l2_norm(values):
    return math.sqrt(sum(v * v for v in values))


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def setup_module(module):  # noqa: D401
    os.environ.setdefault("SUPABASE_DB_URL", "postgresql://user:pass@localhost:5432/db?sslmode=require")
    os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")


def test_mock_embedding_length_and_norm_english():
    from backend.services.embeddings import get_embedding

    vec = run(get_embedding("hello world", provider="mock"))
    assert len(vec) == 1024
    norm = _l2_norm(vec)
    assert 0.99 <= norm <= 1.01


def test_mock_embedding_length_and_norm_arabic():
    from backend.services.embeddings import get_embedding

    text = "مرحبا بالعالم"
    vec = run(get_embedding(text, provider="mock"))
    assert len(vec) == 1024
    norm = _l2_norm(vec)
    assert 0.99 <= norm <= 1.01


