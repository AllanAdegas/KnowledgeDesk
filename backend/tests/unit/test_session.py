"""Unit tests for backend.chatbot.session. Uses a per-test SQLite file via
the autouse `isolated_database` fixture — no shared state between tests.
"""

import uuid

import pytest

from chatbot.session import add_message, create_session, get_history


@pytest.mark.asyncio
async def test_create_session_returns_uuid() -> None:
    session_id = await create_session()

    assert uuid.UUID(session_id)


@pytest.mark.asyncio
async def test_add_and_get_messages() -> None:
    session_id = await create_session()

    await add_message(session_id, "user", "Olá")
    await add_message(session_id, "assistant", "Oi, como posso ajudar?")

    history = await get_history(session_id)

    assert history == [
        {"role": "user", "content": "Olá"},
        {"role": "assistant", "content": "Oi, como posso ajudar?"},
    ]


@pytest.mark.asyncio
async def test_get_history_starts_empty_for_new_session() -> None:
    session_id = await create_session()

    history = await get_history(session_id)

    assert history == []


@pytest.mark.asyncio
async def test_history_limited_to_max_turns() -> None:
    session_id = await create_session()

    for i in range(15):
        await add_message(session_id, "user", f"message {i}")

    history = await get_history(session_id, limit=10)

    assert len(history) == 10
    # Sliding window: only the 10 most recent messages, oldest-first order.
    assert history[0]["content"] == "message 5"
    assert history[-1]["content"] == "message 14"
