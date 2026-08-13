"""Unit tests for backend.rag.pipeline streaming behavior."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from core.config import settings
from core.ollama_client import OllamaClient
from rag.ingestion import ingest_document
from rag.pipeline import NOT_FOUND_MESSAGE, rag_query_stream


@pytest.fixture(autouse=True)
def _isolated_chroma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chroma_persist_dir", str(tmp_path / "chroma"))


@pytest.fixture
def fake_ollama() -> AsyncMock:
    mock = AsyncMock(spec=OllamaClient)
    mock.embed.return_value = [1.0] + [0.0] * 767

    async def _answer_stream(*_args: object, **_kwargs: object):
        for token in ["a resposta", " completa"]:
            yield token

    mock.chat.side_effect = lambda *args, **kwargs: _answer_stream()
    return mock


@pytest.mark.asyncio
async def test_rag_query_stream_yields_tokens_then_sources(
    tmp_path: Path, fake_ollama: AsyncMock
) -> None:
    txt_path = tmp_path / "handbook.txt"
    txt_path.write_text("vacation policy details " * 40, encoding="utf-8")
    await ingest_document(str(txt_path), "handbook.txt", ollama_client=fake_ollama)

    chunks = [chunk async for chunk in rag_query_stream("vacation policy", ollama_client=fake_ollama)]

    joined = "".join(chunks)
    assert "a resposta" in joined
    assert "Fontes: handbook.txt" in joined


@pytest.mark.asyncio
async def test_rag_query_stream_yields_not_found_when_nothing_indexed(
    fake_ollama: AsyncMock,
) -> None:
    chunks = [chunk async for chunk in rag_query_stream("qualquer coisa", ollama_client=fake_ollama)]

    assert chunks == [NOT_FOUND_MESSAGE]
