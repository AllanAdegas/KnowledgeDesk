"""Integration tests for the /api/chat routes. Ollama is fully mocked via
the mock_ollama fixture; SQLite is isolated per test (autouse fixture).
"""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from core.config import settings


@pytest.fixture(autouse=True)
def _isolated_chroma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chroma_persist_dir", str(tmp_path / "chroma"))


def _stream_of(tokens: list[str]) -> AsyncGenerator[str, None]:
    async def _gen() -> AsyncGenerator[str, None]:
        for token in tokens:
            yield token

    return _gen()


@pytest.mark.asyncio
async def test_create_session_returns_id(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/chat/session")

    assert response.status_code == 200
    assert "session_id" in response.json()


@pytest.mark.asyncio
async def test_message_returns_sse_stream(api_client: AsyncClient, mock_ollama: AsyncMock) -> None:
    mock_ollama.chat.return_value = _stream_of(["Olá", " mundo", "!"])
    session_response = await api_client.post("/api/chat/session")
    session_id = session_response.json()["session_id"]

    response = await api_client.post(
        "/api/chat/message", json={"session_id": session_id, "message": "oi"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert '"type": "token"' in response.text
    assert '"type": "done"' in response.text
    assert session_id in response.text


@pytest.mark.asyncio
async def test_history_persists_across_messages(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    mock_ollama.chat.return_value = _stream_of(["resposta"])
    session_response = await api_client.post("/api/chat/session")
    session_id = session_response.json()["session_id"]

    await api_client.post(
        "/api/chat/message", json={"session_id": session_id, "message": "primeira pergunta"}
    )

    history_response = await api_client.get(f"/api/chat/history/{session_id}")
    history = history_response.json()

    assert history_response.status_code == 200
    assert history[0] == {"role": "user", "content": "primeira pergunta"}
    assert history[1] == {"role": "assistant", "content": "resposta"}


@pytest.mark.asyncio
async def test_history_window_limited_to_10_turns(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    session_response = await api_client.post("/api/chat/session")
    session_id = session_response.json()["session_id"]

    for i in range(6):
        mock_ollama.chat.return_value = _stream_of([f"resposta {i}"])
        await api_client.post(
            "/api/chat/message", json={"session_id": session_id, "message": f"pergunta {i}"}
        )

    # 6 exchanges * 2 messages each = 12 stored messages total.
    full_history_response = await api_client.get(f"/api/chat/history/{session_id}")
    assert len(full_history_response.json()) == 12

    # get_history's sliding window (used internally by streaming) still
    # returns only the most recent max_history_turns=10 messages.
    from chatbot.session import get_history

    windowed = await get_history(session_id, limit=10)
    assert len(windowed) == 10
    # 12 messages total, most recent 10 -> the oldest 2 (pergunta 0, resposta 0) drop off.
    assert windowed[0]["content"] == "pergunta 1"


@pytest.mark.asyncio
async def test_message_with_rag_enabled_cites_source(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    files = {"file": ("policy.txt", b"remote work policy details " * 30, "text/plain")}
    await api_client.post("/api/documents/upload", files=files)

    mock_ollama.chat.return_value = _stream_of(["a resposta baseada no documento"])
    session_response = await api_client.post("/api/chat/session")
    session_id = session_response.json()["session_id"]

    response = await api_client.post(
        "/api/chat/message",
        json={"session_id": session_id, "message": "qual a política?", "rag_enabled": True},
    )

    assert response.status_code == 200
    assert "policy.txt" in response.text
    assert '"type": "done"' in response.text
