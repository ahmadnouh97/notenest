from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


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

app = FastAPI(title="notenest-backend", version="0.0.1")


def _parse_allowed_origins(value: str | None) -> List[str]:
    if not value:
        return []
    return [origin.strip() for origin in value.split(",") if origin.strip()]


allowed_origins = _parse_allowed_origins(
    os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    )
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "version": app.version}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


