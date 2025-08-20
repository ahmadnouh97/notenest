from __future__ import annotations

import asyncio
import os
import re
import ssl as ssl_module
from typing import Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import asyncpg

from .settings import get_settings

try:  # Optional certifi for robust CA bundle
    import certifi  # type: ignore
except Exception:  # pragma: no cover
    certifi = None  # type: ignore


class DatabasePool:
    """Holds a global asyncpg pool for the application lifecycle."""

    def __init__(self) -> None:
        self._pool: Optional[asyncpg.Pool] = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database pool not initialized yet")
        return self._pool

    async def connect(self) -> None:
        settings = get_settings()
        # Sanitize DSN: remove any whitespace/newlines and enforce sslmode=require
        dsn_raw = settings.supabase_db_url
        dsn_clean = re.sub(r"\s+", "", dsn_raw)
        parsed = urlparse(dsn_clean)
        if parsed.scheme not in ("postgresql", "postgres"):
            raise RuntimeError(
                "SUPABASE_DB_URL must be a Postgres DSN starting with postgresql://"
            )
        # Ensure sslmode=require in query
        query_items = dict(parse_qsl(parsed.query, keep_blank_values=True))
        # Normalize common typo
        if "slmode" in query_items and "sslmode" not in query_items:
            query_items["sslmode"] = query_items.pop("slmode")
        query_items.setdefault("sslmode", "require")
        sanitized_dsn = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                urlencode(query_items, doseq=True),
                parsed.fragment,
            )
        )
        # Create SSL context with robust certificate verification
        try:
            ssl_ctx = ssl_module.create_default_context()
            if certifi is not None:
                # Use certifi's CA bundle which includes AWS/Supabase certificates
                ssl_ctx = ssl_module.create_default_context(cafile=certifi.where())
        except Exception:
            # Fallback to default context
            ssl_ctx = ssl_module.create_default_context()
        try:
            self._pool = await asyncpg.create_pool(
                dsn=sanitized_dsn,
                min_size=1,
                max_size=10,
                ssl=ssl_ctx,
                timeout=30.0,
            )
            # Simple health check
            async with self._pool.acquire() as conn:
                await conn.execute("select 1;")
        except Exception as exc:  # pragma: no cover
            host = parsed.hostname or "<unknown>"
            # Optional insecure fallback controlled by env var for local debugging
            if os.getenv("PGSSL_INSECURE", "false").lower() in ("1", "true", "yes"):
                insecure_ctx = ssl_module.SSLContext(ssl_module.PROTOCOL_TLS_CLIENT)
                insecure_ctx.check_hostname = False
                insecure_ctx.verify_mode = ssl_module.CERT_NONE
                self._pool = await asyncpg.create_pool(
                    dsn=sanitized_dsn,
                    min_size=1,
                    max_size=10,
                    ssl=insecure_ctx,
                    timeout=30.0,
                )
                async with self._pool.acquire() as conn:
                    await conn.execute("select 1;")
                return
            raise RuntimeError(
                f"Failed to connect to Postgres at host '{host}'. Check SUPABASE_DB_URL (Project settings → Database → Connection string → URI), DNS/IPv6, and local TLS interception software. If needed temporarily, set PGSSL_INSECURE=true to bypass verification. Original error: {exc}"
            ) from exc

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None


db_pool = DatabasePool()


