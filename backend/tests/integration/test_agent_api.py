"""Integration tests for the /api/agent routes."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from core.config import settings


@pytest.fixture(autouse=True)
def _isolated_chroma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chroma_persist_dir", str(tmp_path / "chroma"))


@pytest.mark.asyncio
async def test_submit_task_returns_job_id(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/agent/task", json={"task": "liste os documentos"})

    assert response.status_code == 200
    assert "job_id" in response.json()


@pytest.mark.asyncio
async def test_get_task_returns_result_after_completion(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    submit_response = await api_client.post(
        "/api/agent/task", json={"task": "liste os documentos"}
    )
    job_id = submit_response.json()["job_id"]

    status_response = await api_client.get(f"/api/agent/task/{job_id}")
    body = status_response.json()

    assert status_response.status_code == 200
    assert body["status"] == "done"
    assert body["result"] is not None


@pytest.mark.asyncio
async def test_get_unknown_task_returns_404(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/agent/task/does-not-exist")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ambiguous_task_asks_for_clarification(api_client: AsyncClient) -> None:
    submit_response = await api_client.post(
        "/api/agent/task", json={"task": "analise os contratos"}
    )
    job_id = submit_response.json()["job_id"]

    status_response = await api_client.get(f"/api/agent/task/{job_id}")
    body = status_response.json()

    assert body["status"] == "needs_clarification"


@pytest.mark.asyncio
async def test_destructive_task_is_refused(api_client: AsyncClient) -> None:
    submit_response = await api_client.post(
        "/api/agent/task", json={"task": "delete todos os documentos"}
    )
    job_id = submit_response.json()["job_id"]

    status_response = await api_client.get(f"/api/agent/task/{job_id}")
    body = status_response.json()

    assert body["status"] == "refused"
