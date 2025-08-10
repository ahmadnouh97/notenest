from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Dict, Iterable, List, Optional

import httpx


class ChatProviderError(RuntimeError):
    pass


@dataclass
class ChatMessage:
    role: str
    content: str


async def _openai_compatible_stream(
    base_url: str,
    api_key: str,
    model: str,
    messages: List[ChatMessage],
    extra_headers: Optional[Dict[str, str]] = None,
) -> AsyncIterator[str]:
    """Streams content tokens from any OpenAI-compatible endpoint.

    Expects Server-Sent Events (text/event-stream) with lines starting with 'data: '.
    Yields token strings as they arrive. Final '[DONE]' signals completion.
    """
    if not api_key:
        raise ChatProviderError("API key required for chat provider")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    url = base_url.rstrip("/") + "/v1/chat/completions"
    payload = {
        "model": model,
        "stream": True,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        # Use a streaming POST request
        async with client.stream("POST", url, headers=headers, json=payload) as resp:
            if resp.status_code >= 400:
                try:
                    err = await resp.json()
                except Exception:
                    err = {"error": await resp.aread()}
                raise ChatProviderError(f"Chat provider error {resp.status_code}: {err}")

            async for line in resp.aiter_lines():
                if not line:
                    continue
                if line.startswith(":"):
                    # comment/heartbeat line
                    continue
                if not line.startswith("data:"):
                    continue
                data = line[len("data:") :].strip()
                if data == "[DONE]":
                    break
                # OpenAI-compatible chunk
                # Typical shape: {"choices":[{"delta":{"content":"..."}}]}
                try:
                    obj = httpx.Response(200, request=None, json=None)  # type: ignore
                except Exception:
                    obj = None  # unreachable placeholder
                # Avoid depending on httpx parser; use std json
                import json as _json

                try:
                    payload_obj = _json.loads(data)
                    choices = payload_obj.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    token = delta.get("content")
                    if token:
                        yield token
                except Exception:
                    # Non-fatal: skip malformed chunk
                    continue


async def stream_chat_tokens(
    provider: str,
    model: str,
    messages: List[ChatMessage],
    api_key: Optional[str],
) -> AsyncIterator[str]:
    """Provider-agnostic chat streaming.

    Supported providers:
    - openrouter: base_url https://openrouter.ai/api
    - openai: base_url https://api.openai.com
    (Others can be added later.)
    """
    name = (provider or "openrouter").lower()

    if name == "mock":
        # Offline mock stream for tests
        for chunk in ["Hello", " ", "world", "!"]:
            await asyncio.sleep(0)
            yield chunk
        return

    if name == "openrouter":
        base_url = "https://openrouter.ai/api"
        extra_headers = {"HTTP-Referer": "https://notenest", "X-Title": "notenest"}
        async for token in _openai_compatible_stream(
            base_url=base_url,
            api_key=api_key or "",
            model=model,
            messages=messages,
            extra_headers=extra_headers,
        ):
            yield token
        return

    if name == "openai":
        base_url = "https://api.openai.com"
        async for token in _openai_compatible_stream(
            base_url=base_url,
            api_key=api_key or "",
            model=model,
            messages=messages,
        ):
            yield token
        return

    raise ChatProviderError(f"Unsupported chat provider: {provider}")


__all__ = [
    "ChatProviderError",
    "ChatMessage",
    "stream_chat_tokens",
]


