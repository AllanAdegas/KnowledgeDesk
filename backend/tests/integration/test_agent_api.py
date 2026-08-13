"""Integration tests for the /api/agent routes."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from core.config import settings


@pytest.fixture(autouse=True)
def _isolated_chroma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chroma_persist_dir", str(tmp_path / "chroma"))


async def _json_response(text: str) -> AsyncGenerator[str, None]:
    yield text


def _mock_llm_classification(mock_ollama: AsyncMock, category: str, target_hint: str | None = None) -> None:
    """Make the mocked Ollama's chat() return a valid structured classification.

    `side_effect` (not `return_value`) is used so a fresh generator is built
    on every call — tasks that reach the summarize tool call `chat()` a
    second time (for the actual summary), which would otherwise consume an
    already-exhausted generator.
    """
    hint_json = "null" if target_hint is None else f'"{target_hint}"'
    payload = f'{{"category": "{category}", "target_hint": {hint_json}}}'
    mock_ollama.chat.side_effect = lambda *args, **kwargs: _json_response(payload)


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


@pytest.mark.asyncio
async def test_list_task_phrased_naturally_via_llm(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    _mock_llm_classification(mock_ollama, "list")

    submit_response = await api_client.post(
        "/api/agent/task", json={"task": "mostra os documentos que eu tenho"}
    )
    job_id = submit_response.json()["job_id"]

    status_response = await api_client.get(f"/api/agent/task/{job_id}")
    body = status_response.json()

    assert body["status"] == "done"


@pytest.mark.asyncio
async def test_destructive_task_phrased_naturally_via_llm(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    _mock_llm_classification(mock_ollama, "destructive")

    submit_response = await api_client.post(
        "/api/agent/task", json={"task": "apaga tudo, por favor"}
    )
    job_id = submit_response.json()["job_id"]

    status_response = await api_client.get(f"/api/agent/task/{job_id}")
    body = status_response.json()

    assert body["status"] == "refused"


@pytest.mark.asyncio
async def test_ambiguous_task_phrased_naturally_via_llm(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    _mock_llm_classification(mock_ollama, "ambiguous")

    submit_response = await api_client.post(
        "/api/agent/task", json={"task": "me ajuda com isso aqui"}
    )
    job_id = submit_response.json()["job_id"]

    status_response = await api_client.get(f"/api/agent/task/{job_id}")
    body = status_response.json()

    assert body["status"] == "needs_clarification"


@pytest.mark.asyncio
async def test_summarize_task_resolves_target_document_by_name(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    mock_ollama.embed.return_value = [0.1] * 768
    files = {"file": ("sample.txt", b"quarterly sales figures " * 40, "text/plain")}
    await api_client.post("/api/documents/upload", files=files)

    _mock_llm_classification(mock_ollama, "summarize", target_hint="sample.txt")

    submit_response = await api_client.post(
        "/api/agent/task", json={"task": "quero um resumo do sample.txt"}
    )
    job_id = submit_response.json()["job_id"]

    status_response = await api_client.get(f"/api/agent/task/{job_id}")
    body = status_response.json()

    assert body["status"] == "done"
    assert body["result"]


@pytest.mark.asyncio
async def test_task_citing_unknown_document_asks_for_clarification(
    api_client: AsyncClient, mock_ollama: AsyncMock
) -> None:
    _mock_llm_classification(mock_ollama, "summarize", target_hint="contrato-fantasma.pdf")

    submit_response = await api_client.post(
        "/api/agent/task", json={"task": "resuma o contrato-fantasma.pdf"}
    )
    job_id = submit_response.json()["job_id"]

    status_response = await api_client.get(f"/api/agent/task/{job_id}")
    body = status_response.json()

    assert body["status"] == "needs_clarification"
    assert "contrato-fantasma.pdf" in body["result"]
