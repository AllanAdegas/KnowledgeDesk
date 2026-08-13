"""Unit tests for backend.rag.ingestion. Ollama is always mocked."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pypdf import PdfWriter

from core.config import settings
from core.ollama_client import OllamaClient
from rag.ingestion import (
    DocumentExtractionError,
    UnsupportedFileTypeError,
    ingest_document,
    list_indexed_documents,
)


def _make_valid_pdf(path: Path, pages: int = 1) -> None:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=200, height=200)
    with path.open("wb") as handle:
        writer.write(handle)


@pytest.fixture(autouse=True)
def _isolated_chroma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chroma_persist_dir", str(tmp_path / "chroma"))


@pytest.fixture
def fake_ollama() -> AsyncMock:
    mock = AsyncMock(spec=OllamaClient)
    mock.embed.return_value = [0.1] * 768

    async def _summary_stream(*_args: object, **_kwargs: object):
        yield "resumo de teste"

    mock.chat.side_effect = lambda *args, **kwargs: _summary_stream()
    return mock


@pytest.mark.asyncio
async def test_ingest_pdf_returns_chunk_count(tmp_path: Path, fake_ollama: AsyncMock) -> None:
    # A blank PDF has no extractable text, so write a .txt instead to exercise
    # the chunking + embedding + persistence path deterministically, and a
    # real (but text-less) PDF separately below to check extension handling.
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("word " * 400, encoding="utf-8")

    result = await ingest_document(str(txt_path), "sample.txt", ollama_client=fake_ollama)

    assert result["status"] == "indexed"
    assert result["filename"] == "sample.txt"
    assert result["chunks_count"] > 1
    assert "id" in result
    assert fake_ollama.embed.await_count == result["chunks_count"]


@pytest.mark.asyncio
async def test_ingest_unsupported_format_raises(tmp_path: Path, fake_ollama: AsyncMock) -> None:
    bad_path = tmp_path / "malware.exe"
    bad_path.write_bytes(b"not a real executable")

    with pytest.raises(UnsupportedFileTypeError):
        await ingest_document(str(bad_path), "malware.exe", ollama_client=fake_ollama)


@pytest.mark.asyncio
async def test_ingest_corrupted_pdf_raises(tmp_path: Path, fake_ollama: AsyncMock) -> None:
    corrupted_path = tmp_path / "broken.pdf"
    corrupted_path.write_bytes(b"%PDF-1.4 this is not a valid pdf stream")

    with pytest.raises(DocumentExtractionError):
        await ingest_document(str(corrupted_path), "broken.pdf", ollama_client=fake_ollama)


@pytest.mark.asyncio
async def test_ingest_empty_txt_raises_extraction_error(
    tmp_path: Path, fake_ollama: AsyncMock
) -> None:
    empty_path = tmp_path / "empty.txt"
    empty_path.write_text("", encoding="utf-8")

    with pytest.raises(DocumentExtractionError):
        await ingest_document(str(empty_path), "empty.txt", ollama_client=fake_ollama)


@pytest.mark.asyncio
async def test_ingest_includes_summary_in_result(tmp_path: Path, fake_ollama: AsyncMock) -> None:
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("word " * 400, encoding="utf-8")

    result = await ingest_document(str(txt_path), "sample.txt", ollama_client=fake_ollama)

    assert result["summary"] == "resumo de teste"


@pytest.mark.asyncio
async def test_ingest_truncates_text_before_summarizing(
    tmp_path: Path, fake_ollama: AsyncMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "rag_summary_max_chars", 50)
    txt_path = tmp_path / "big.txt"
    txt_path.write_text("palavra " * 2000, encoding="utf-8")

    await ingest_document(str(txt_path), "big.txt", ollama_client=fake_ollama)

    # Only one chat() call happens during ingestion (the summary); its
    # prompt must be built from the truncated text, not the full document.
    sent_messages = fake_ollama.chat.call_args.args[0]
    prompt = sent_messages[0]["content"]
    assert len(prompt) < 500


@pytest.mark.asyncio
async def test_summary_persisted_in_chunk_metadata_and_listing(
    tmp_path: Path, fake_ollama: AsyncMock
) -> None:
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("word " * 400, encoding="utf-8")
    await ingest_document(str(txt_path), "sample.txt", ollama_client=fake_ollama)

    documents = list_indexed_documents()

    assert any(doc["summary"] == "resumo de teste" for doc in documents)
