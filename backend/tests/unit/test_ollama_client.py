"""Unit tests for OllamaClient. All HTTP calls are mocked via respx-free
monkeypatching of httpx.AsyncClient methods — no real network access.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from core.ollama_client import OllamaClient


class _FakeResponse:
    def __init__(self, json_data: dict[str, Any]) -> None:
        self._json_data = json_data

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._json_data


@pytest.mark.asyncio
async def test_chat_non_streaming_returns_full_message(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = _FakeResponse({"message": {"content": "olá mundo"}})
    mock_post = AsyncMock(return_value=fake_response)
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    monkeypatch.setattr(httpx.AsyncClient, "__aenter__", AsyncMock(return_value=None))
    monkeypatch.setattr(httpx.AsyncClient, "__aexit__", AsyncMock(return_value=False))

    async def fake_aenter(self: httpx.AsyncClient) -> httpx.AsyncClient:
        return self

    monkeypatch.setattr(httpx.AsyncClient, "__aenter__", fake_aenter)

    client = OllamaClient(base_url="http://fake", chat_model="llama3.2")
    chunks = [chunk async for chunk in client.chat([{"role": "user", "content": "oi"}], stream=False)]

    assert chunks == ["olá mundo"]
    mock_post.assert_awaited_once()


@pytest.mark.asyncio
async def test_embed_returns_vector(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = _FakeResponse({"embedding": [0.1, 0.2, 0.3]})
    mock_post = AsyncMock(return_value=fake_response)
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    async def fake_aenter(self: httpx.AsyncClient) -> httpx.AsyncClient:
        return self

    monkeypatch.setattr(httpx.AsyncClient, "__aenter__", fake_aenter)
    monkeypatch.setattr(httpx.AsyncClient, "__aexit__", AsyncMock(return_value=False))

    client = OllamaClient(base_url="http://fake", embed_model="nomic-embed-text")
    embedding = await client.embed("hello")

    assert embedding == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_list_models_returns_names(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_response = _FakeResponse({"models": [{"name": "llama3.2"}, {"name": "mistral"}]})
    mock_get = AsyncMock(return_value=fake_response)
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    async def fake_aenter(self: httpx.AsyncClient) -> httpx.AsyncClient:
        return self

    monkeypatch.setattr(httpx.AsyncClient, "__aenter__", fake_aenter)
    monkeypatch.setattr(httpx.AsyncClient, "__aexit__", AsyncMock(return_value=False))

    client = OllamaClient(base_url="http://fake")
    models = await client.list_models()

    assert models == ["llama3.2", "mistral"]


@pytest.mark.asyncio
async def test_chat_streaming_yields_incremental_chunks(monkeypatch: pytest.MonkeyPatch) -> None:
    lines = [
        '{"message": {"content": "olá"}, "done": false}',
        '{"message": {"content": " mundo"}, "done": false}',
        '{"message": {"content": ""}, "done": true}',
    ]

    class _FakeStreamCtx:
        async def __aenter__(self) -> "_FakeStreamCtx":
            return self

        async def __aexit__(self, *args: object) -> bool:
            return False

        def raise_for_status(self) -> None:
            return None

        async def aiter_lines(self) -> Any:
            for line in lines:
                yield line

    def fake_stream(self: httpx.AsyncClient, method: str, url: str, **kwargs: Any) -> _FakeStreamCtx:
        return _FakeStreamCtx()

    async def fake_aenter(self: httpx.AsyncClient) -> httpx.AsyncClient:
        return self

    monkeypatch.setattr(httpx.AsyncClient, "__aenter__", fake_aenter)
    monkeypatch.setattr(httpx.AsyncClient, "__aexit__", AsyncMock(return_value=False))
    monkeypatch.setattr(httpx.AsyncClient, "stream", fake_stream)

    client = OllamaClient(base_url="http://fake", chat_model="llama3.2")
    chunks = [chunk async for chunk in client.chat([{"role": "user", "content": "oi"}], stream=True)]

    assert chunks == ["olá", " mundo"]


def test_ollama_client_defaults_come_from_settings() -> None:
    client = OllamaClient()
    assert client.base_url == "http://localhost:11434"
    assert client.chat_model == "llama3.2"
    assert client.embed_model == "nomic-embed-text"


def test_ollama_client_accepts_overrides() -> None:
    client = OllamaClient(base_url="http://other:1234", chat_model="mistral", embed_model="custom-embed")
    assert client.base_url == "http://other:1234"
    assert client.chat_model == "mistral"
    assert client.embed_model == "custom-embed"


@pytest.mark.asyncio
async def test_mock_ollama_fixture_chat_streams_expected_tokens(mock_ollama: MagicMock) -> None:
    chunks = [chunk async for chunk in mock_ollama.chat([{"role": "user", "content": "oi"}])]
    assert chunks == ["Olá", " mundo", "!"]


@pytest.mark.asyncio
async def test_mock_ollama_fixture_embed_returns_fixed_vector(mock_ollama: MagicMock) -> None:
    vector = await mock_ollama.embed("qualquer texto")
    assert len(vector) == 768
