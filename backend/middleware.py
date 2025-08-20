from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory per-IP token bucket.

    Not suitable for multi-process deployments without shared state, but OK for free-tier
    single-instance setups. Configure endpoints by path prefix list to protect heavy routes.
    """

    def __init__(
        self,
        app,
        *,
        capacity: int = 30,
        refill_per_second: float = 1.0,
        protected_prefixes: Optional[list[str]] = None,
    ) -> None:
        super().__init__(app)
        self.capacity = float(capacity)
        self.refill_per_second = float(refill_per_second)
        self.protected_prefixes = protected_prefixes or [
            "/api/search",
            "/api/chat",
            "/api/notes",
        ]
        self._buckets: Dict[str, _Bucket] = {}

    def _is_protected(self, path: str) -> bool:
        for prefix in self.protected_prefixes:
            if path.startswith(prefix):
                return True
        return False

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Bypass non-protected routes
        path = request.url.path
        if not self._is_protected(path):
            return await call_next(request)

        # Identify client IP (trusting headers is out-of-scope for free-tier demo)
        client_host = request.client.host if request.client else "unknown"

        now = time.monotonic()
        bucket = self._buckets.get(client_host)
        if bucket is None:
            bucket = _Bucket(tokens=self.capacity, last_refill=now)
            self._buckets[client_host] = bucket
        else:
            # Refill tokens since last request
            elapsed = max(0.0, now - bucket.last_refill)
            bucket.tokens = min(self.capacity, bucket.tokens + elapsed * self.refill_per_second)
            bucket.last_refill = now

        if bucket.tokens < 1.0:
            # Too many requests
            from fastapi.responses import JSONResponse

            retry_after = max(1, int(1.0 / self.refill_per_second))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )

        bucket.tokens -= 1.0
        return await call_next(request)


__all__ = ["RateLimitMiddleware"]


