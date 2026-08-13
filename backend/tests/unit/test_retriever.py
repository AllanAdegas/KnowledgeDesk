"""Unit tests for backend.rag.retriever. Ollama and Chroma queries are mocked
via an isolated per-test persist directory plus an injected fake client.
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from core.config import settings
from core.ollama_client import OllamaClient
from rag.ingestion import ingest_document
from rag.retriever import retrieve


@pytest.fixture(autouse=True)
def _isolated_chroma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chroma_persist_dir", str(tmp_path / "chroma"))


@pytest.fixture
def fake_ollama() -> AsyncMock:
    """An Ollama mock that returns a fixed, distinguishable embedding per call."""
    mock = AsyncMock(spec=OllamaClient)
    mock.embed.return_value = [1.0] + [0.0] * 767

    async def _summary_stream(*_args: object, **_kwargs: object):
        yield "resumo de teste"

    mock.chat.side_effect = lambda *args, **kwargs: _summary_stream()
    return mock


@pytest.mark.asyncio
async def test_retrieve_returns_top_k_results(tmp_path: Path, fake_ollama: AsyncMock) -> None:
    txt_path = tmp_path / "doc.txt"
    txt_path.write_text("word " * 400, encoding="utf-8")
    await ingest_document(str(txt_path), "doc.txt", ollama_client=fake_ollama)

    results = await retrieve("word", k=2, score_threshold=0.0, ollama_client=fake_ollama)

    assert len(results) <= 2
    assert all(result.score >= 0.0 for result in results)


@pytest.mark.asyncio
async def test_retrieve_filters_low_score_results(tmp_path: Path, fake_ollama: AsyncMock) -> None:
    txt_path = tmp_path / "doc.txt"
    txt_path.write_text("word " * 400, encoding="utf-8")
    await ingest_document(str(txt_path), "doc.txt", ollama_client=fake_ollama)

    # Query embedding identical to document embedding -> distance 0 -> score 1.0,
    # so an unreachable threshold above 1.0 must filter every result out.
    results = await retrieve("word", k=5, score_threshold=1.5, ollama_client=fake_ollama)

    assert results == []


@pytest.mark.asyncio
async def test_retrieve_empty_when_no_match(tmp_path: Path, fake_ollama: AsyncMock) -> None:
    # No documents ingested at all -> empty collection -> empty results.
    results = await retrieve("anything", ollama_client=fake_ollama)

    assert results == []
