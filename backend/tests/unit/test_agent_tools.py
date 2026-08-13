"""Unit tests for agent tools and the LangGraph agent's control flow.
Ollama is always mocked; Chroma is isolated per test.
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from agents.graph import classify_task, run_agent_task
from agents.tools.list_docs import list_docs
from agents.tools.search_docs import search_docs
from agents.tools.summarize import summarize
from core.config import settings
from core.ollama_client import OllamaClient
from rag.ingestion import ingest_document


@pytest.fixture(autouse=True)
def _isolated_chroma(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "chroma_persist_dir", str(tmp_path / "chroma"))


@pytest.fixture
def fake_ollama() -> AsyncMock:
    # spec=OllamaClient matters here: since OllamaClient.chat is an async
    # *generator* function (not a coroutine function), unittest.mock inspects
    # the spec and makes `mock.chat(...)` a plain (synchronous) call that
    # returns `.return_value`/`side_effect(...)` directly — exactly like the
    # real client, where `async for token in client.chat(...)` never awaits
    # the call itself. Without spec, AsyncMock would wrap chat() as a
    # coroutine and break every `async for` call site.
    mock = AsyncMock(spec=OllamaClient)
    mock.embed.return_value = [1.0] + [0.0] * 767

    async def _summary_stream(*_args: object, **_kwargs: object):
        for token in ["- ponto 1", " - ponto 2"]:
            yield token

    mock.chat.side_effect = lambda *args, **kwargs: _summary_stream()
    return mock


@pytest.mark.asyncio
async def test_search_docs_tool_calls_retriever(tmp_path: Path, fake_ollama: AsyncMock) -> None:
    txt_path = tmp_path / "policy.txt"
    txt_path.write_text("remote work policy details " * 40, encoding="utf-8")
    await ingest_document(str(txt_path), "policy.txt", ollama_client=fake_ollama)

    results = await search_docs("remote work", ollama_client=fake_ollama)

    assert len(results) > 0
    assert results[0]["filename"] == "policy.txt"


@pytest.mark.asyncio
async def test_list_docs_returns_all_documents(tmp_path: Path, fake_ollama: AsyncMock) -> None:
    txt_path = tmp_path / "handbook.txt"
    txt_path.write_text("employee handbook content " * 30, encoding="utf-8")
    await ingest_document(str(txt_path), "handbook.txt", ollama_client=fake_ollama)

    documents = list_docs()

    assert any(doc["filename"] == "handbook.txt" for doc in documents)


@pytest.mark.asyncio
async def test_summarize_tool_returns_llm_output(fake_ollama: AsyncMock) -> None:
    summary = await summarize("um texto longo qualquer", ollama_client=fake_ollama)

    assert summary == "- ponto 1 - ponto 2"


def test_classify_task_detects_destructive_intent() -> None:
    assert classify_task("delete os documentos") == "destructive"


def test_classify_task_detects_list_intent() -> None:
    assert classify_task("liste todos os documentos sobre RH") == "list"


def test_classify_task_detects_summarize_intent() -> None:
    assert classify_task("resuma o documento X e extraia os pontos principais") == "summarize"


def test_classify_task_falls_back_to_ambiguous() -> None:
    assert classify_task("analise os contratos") == "ambiguous"


@pytest.mark.asyncio
async def test_agent_requests_clarification_for_ambiguous_task(fake_ollama: AsyncMock) -> None:
    state = await run_agent_task("analise os contratos", ollama_client=fake_ollama)

    assert state["status"] == "needs_clarification"
    assert state["result"] is not None


@pytest.mark.asyncio
async def test_agent_refuses_destructive_task(fake_ollama: AsyncMock) -> None:
    state = await run_agent_task("delete os documentos", ollama_client=fake_ollama)

    assert state["status"] == "refused"
    assert "leitura" in (state["result"] or "").lower()


@pytest.mark.asyncio
async def test_agent_lists_documents_for_list_task(
    tmp_path: Path, fake_ollama: AsyncMock
) -> None:
    txt_path = tmp_path / "rh.txt"
    txt_path.write_text("politica de RH " * 30, encoding="utf-8")
    await ingest_document(str(txt_path), "rh.txt", ollama_client=fake_ollama)

    state = await run_agent_task("liste todos os documentos sobre RH", ollama_client=fake_ollama)

    assert state["status"] == "done"
    assert "rh.txt" in (state["result"] or "")


@pytest.mark.asyncio
async def test_agent_stops_after_max_iterations(fake_ollama: AsyncMock) -> None:
    # No documents indexed -> search_docs always returns [] -> the graph
    # loops plan<->execute_tools until the iteration cap is hit.
    state = await run_agent_task(
        "resuma o documento inexistente e seus pontos principais", ollama_client=fake_ollama
    )

    assert state["status"] == "max_iterations_reached"
    assert state["iterations"] == settings.agent_max_iterations
    assert state["result"] is not None
