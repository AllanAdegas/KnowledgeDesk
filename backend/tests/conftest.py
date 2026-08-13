"""Global pytest fixtures.

Every automated test in this suite mocks `OllamaClient` — none of them ever
perform a real network call to a running Ollama server, per project policy.
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.ollama_client import OllamaClient


async def _async_generator(chunks: list[str]) -> AsyncGenerator[str, None]:
    for chunk in chunks:
        yield chunk


@pytest.fixture
def mock_ollama(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Replace the module-level Ollama singleton with a fully mocked client."""
    mock = AsyncMock(spec=OllamaClient)
    mock.chat.return_value = _async_generator(["Olá", " mundo", "!"])
    mock.embed.return_value = [0.1] * 768
    mock.list_models.return_value = ["llama3.2", "nomic-embed-text"]

    monkeypatch.setattr("core.ollama_client.client", mock)
    return mock


@pytest_asyncio.fixture
async def api_client(mock_ollama: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    """An httpx AsyncClient wired to the FastAPI app via ASGITransport."""
    # Imported lazily so `mock_ollama` patches core.ollama_client.client
    # before any route module resolves its own reference to it.
    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as test_client:
        yield test_client


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
