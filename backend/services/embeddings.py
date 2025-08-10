from __future__ import annotations

import math
from typing import Any, Iterable, List, Optional

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from ..settings import get_settings


DEFAULT_HF_MODEL = "BAAI/bge-m3"


class EmbeddingError(RuntimeError):
    pass


def _flatten_embedding_payload(payload: Any) -> List[float]:
    """Best-effort extraction of a 1-D list[float] from HF Inference API responses.

    HF models can return:
    - list[float]
    - list[list[float]] (batch or token-level)
    - dict with "embeddings": list[float]
    """
    if payload is None:
        raise EmbeddingError("Empty embedding response from provider")

    if isinstance(payload, dict):
        # Some endpoints may return {"embeddings": [...]} or {"data": [...]} shapes
        for key in ("embeddings", "data", "vector"):
            if key in payload:
                return _flatten_embedding_payload(payload[key])
        # Fallthrough: unknown dict shape
        raise EmbeddingError("Unexpected embedding response object shape from provider")

    if isinstance(payload, (list, tuple)):
        if not payload:
            raise EmbeddingError("Embedding response is an empty list")
        first = payload[0]
        if isinstance(first, (list, tuple)):
            # Assume batched shape and take first row
            return [float(x) for x in first]
        # Already a 1-D vector
        return [float(x) for x in payload]

    raise EmbeddingError("Unsupported embedding payload type from provider")


def _l2_normalize(values: Iterable[float]) -> List[float]:
    acc = 0.0
    result = [float(v) for v in values]
    for v in result:
        acc += v * v
    norm = math.sqrt(acc)
    if not math.isfinite(norm) or norm <= 1e-12:
        # Return zeros to signal unusable vector rather than exploding
        return [0.0 for _ in result]
    inv = 1.0 / norm
    for i in range(len(result)):
        result[i] *= inv
    return result


async def _hf_bge_m3_embedding(text: str, api_key: Optional[str]) -> List[float]:
    if not api_key:
        raise EmbeddingError("HF API key is required for HuggingFace embeddings")

    url = f"https://api-inference.huggingface.co/models/{DEFAULT_HF_MODEL}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    json_payload = {
        "inputs": text,
        # Ask HF to auto-load the model on first call
        "options": {"wait_for_model": True},
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        # Retry a few times on transient model loading/timeouts
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(httpx.HTTPError),
            reraise=True,
        ):
            with attempt:
                resp = await client.post(url, headers=headers, json=json_payload)
                # The HF API returns 200 on success; 5xx and 503 for loading
                if resp.status_code >= 400:
                    try:
                        data = resp.json()
                    except Exception:
                        data = {"error": resp.text}
                    message = data.get("error") if isinstance(data, dict) else str(data)
                    raise EmbeddingError(
                        f"HF Inference API error (status={resp.status_code}): {message}"
                    )
                payload = resp.json()
                vector = _flatten_embedding_payload(payload)
                return vector

    # Should not reach here due to reraise=True
    raise EmbeddingError("Unexpected failure to obtain embedding from HF provider")


async def get_embedding(
    text: str,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
) -> List[float]:
    """Get an L2-normalized embedding vector for the input text.

    Provider selection:
    - provider == "hf" (default): uses HuggingFace Inference API with BAAI/bge-m3
    - provider == "mock": deterministic mock vector (for testing without network)
    """
    settings = get_settings()
    chosen = (provider or settings.embed_provider or "hf").lower()

    if chosen == "mock":
        # Deterministic 1024-dim pseudo-embedding for tests (no network, no keys)
        seed_len = float(len(text or ""))
        seed_sum = float(sum(ord(c) for c in (text or ""))) or 1.0
        vec = []
        for i in range(1024):
            val = math.sin(0.017 * (i + 1) * seed_len) + math.cos(0.013 * (i + 7) * seed_sum)
            vec.append(val)
        return _l2_normalize(vec)

    if chosen == "hf":
        key = api_key or settings.hf_api_key
        raw = await _hf_bge_m3_embedding(text, key)
        return _l2_normalize(raw)

    raise EmbeddingError(f"Unsupported embedding provider: {provider}")


__all__ = [
    "EmbeddingError",
    "get_embedding",
    "DEFAULT_HF_MODEL",
]


