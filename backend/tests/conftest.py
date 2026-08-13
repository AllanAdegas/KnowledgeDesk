"""Global pytest fixtures.

Every automated test in this suite mocks `OllamaClient` — none of them ever
perform a real network call to a running Ollama server, per project policy.
"""

from collections.abc import AsyncGenerator
from pathlib import Path
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
    # `side_effect` (not `return_value`) so a fresh generator is built on
    # every call: a single test can trigger chat() more than once (e.g. an
    # upload's post-indexing summary, then a chat/agent call), and a
    # `return_value` generator instance would be exhausted after the first.
    mock.chat.side_effect = lambda *args, **kwargs: _async_generator(["Olá", " mundo", "!"])
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


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the SQLite database at a fresh per-test file.

    `core.database` builds its engine/sessionmaker once at import time, so we
    rebuild the module-level holder here rather than relying on the
    `settings.database_url` value alone (which the already-built engine
    would never re-read).
    """
    import core.database as database_module

    db_path = tmp_path / "test.db"
    monkeypatch.setattr(database_module.settings, "database_url", f"sqlite+aiosqlite:///{db_path}")
    monkeypatch.setattr(database_module, "_engine_holder", database_module.AsyncSessionEngine())
