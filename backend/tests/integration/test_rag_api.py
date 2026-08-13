"""Integration tests for the /api/documents and /api/rag routes.

Uses the api_client fixture (httpx AsyncClient over ASGITransport) with
mock_ollama patched in via conftest — no real Ollama or network call.
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from core.config import settings


@pytest.fixture(autouse=True)
def _isolated_chroma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chroma_persist_dir", str(tmp_path / "chroma"))


@pytest.mark.asyncio
async def test_upload_pdf_returns_indexed_status(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    mock_ollama.embed.return_value = [0.1] * 768
    files = {"file": ("notes.txt", b"word " * 300, "text/plain")}

    response = await api_client.post("/api/documents/upload", files=files)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "indexed"
    assert body["filename"] == "notes.txt"
    assert body["chunks_count"] > 0


@pytest.mark.asyncio
async def test_upload_invalid_format_returns_422(api_client: AsyncClient) -> None:
    files = {"file": ("virus.exe", b"binary content", "application/octet-stream")}

    response = await api_client.post("/api/documents/upload", files=files)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_corrupted_document_returns_400(api_client: AsyncClient) -> None:
    files = {"file": ("empty.txt", b"", "text/plain")}

    response = await api_client.post("/api/documents/upload", files=files)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_rag_query_returns_answer_with_sources(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    mock_ollama.embed.return_value = [0.1] * 768
    files = {"file": ("policy.txt", b"remote work is allowed twice a week " * 20, "text/plain")}
    await api_client.post("/api/documents/upload", files=files)

    response = await api_client.post("/api/rag/query", json={"query": "remote work policy?"})

    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert "policy.txt" in body["sources"]
    assert body["answer"]


@pytest.mark.asyncio
async def test_rag_query_unknown_topic_returns_not_found(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    # No documents uploaded -> collection empty -> nothing can clear threshold.
    response = await api_client.post("/api/rag/query", json={"query": "qualquer coisa"})

    assert response.status_code == 200
    body = response.json()
    assert body["found"] is False
    assert "não encontrei" in body["answer"].lower()


@pytest.mark.asyncio
async def test_list_documents_returns_uploaded_files(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    mock_ollama.embed.return_value = [0.1] * 768
    files = {"file": ("report.txt", b"quarterly numbers " * 50, "text/plain")}
    await api_client.post("/api/documents/upload", files=files)

    response = await api_client.get("/api/documents")

    assert response.status_code == 200
    body = response.json()
    assert any(doc["filename"] == "report.txt" for doc in body)


@pytest.mark.asyncio
async def test_delete_document_removes_it_from_listing(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    mock_ollama.embed.return_value = [0.1] * 768
    files = {"file": ("temp.txt", b"disposable content " * 40, "text/plain")}
    upload_response = await api_client.post("/api/documents/upload", files=files)
    document_id = upload_response.json()["id"]

    delete_response = await api_client.delete(f"/api/documents/{document_id}")
    listing_response = await api_client.get("/api/documents")

    assert delete_response.status_code == 200
    assert all(doc["id"] != document_id for doc in listing_response.json())
