from __future__ import annotations

import asyncio


def test_mock_stream_provider_yields_tokens():
    from backend.services.chat_providers import stream_chat_tokens, ChatMessage

    async def collect():
        parts = []
        async for tok in stream_chat_tokens(
            provider="mock",
            model="dummy",
            messages=[ChatMessage(role="user", content="hi")],
            api_key=None,
        ):
            parts.append(tok)
        return parts

    tokens = asyncio.get_event_loop().run_until_complete(collect())
    assert tokens == ["Hello", " ", "world", "!"]


