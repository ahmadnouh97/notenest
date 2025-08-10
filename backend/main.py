from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import db_pool
from .middleware import RateLimitMiddleware
from .routers.health import router as health_router
from .settings import get_settings


# Load .env from the repo root (or nearest found). On some environments, find_dotenv can
# assert if called from an inline interpreter frame; fall back to explicit path.
_found_env = None
try:
    _found_env = find_dotenv()
except AssertionError:
    pass

if _found_env:
    load_dotenv(_found_env)
else:
    # Try repo root by walking up from this file two levels
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    candidate = os.path.join(repo_root, ".env")
    if os.path.exists(candidate):
        load_dotenv(candidate)

settings = get_settings()

app = FastAPI(title="notenest-backend", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Simple per-IP rate limiting for hot endpoints
app.add_middleware(
    RateLimitMiddleware,
    capacity=30,
    refill_per_second=1.0,
    protected_prefixes=["/api/search", "/api/chat", "/api/notes"],
)


@app.on_event("startup")
async def _startup() -> None:
    await db_pool.connect()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await db_pool.disconnect()


# Routers
app.include_router(health_router)


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


