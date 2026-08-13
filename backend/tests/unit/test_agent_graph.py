"""Unit tests for the hybrid LLM/keyword classification and target-document
resolution in backend.agents.graph. Ollama is always mocked; no test in this
file performs a real network call.
"""

from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest

from agents.graph import (
    ClassificationError,
    ClassificationResult,
    classify_task_hybrid,
    classify_task_llm,
    resolve_target_document,
)
from core.ollama_client import OllamaClient


async def _single_chunk(text: str) -> AsyncGenerator[str, None]:
    yield text


def _ollama_returning(text: str) -> AsyncMock:
    """An OllamaClient mock whose `chat()` always yields a single fixed chunk.

    Uses `side_effect` (not `return_value`) so the generator is rebuilt on
    every call, matching how the real streamed/non-streamed client behaves
    when called more than once in a test.
    """
    mock = AsyncMock(spec=OllamaClient)
    mock.chat.side_effect = lambda *args, **kwargs: _single_chunk(text)
    return mock


@pytest.mark.asyncio
async def test_classify_task_llm_parses_valid_json() -> None:
    ollama = _ollama_returning('{"category": "summarize", "target_hint": "contrato da Acme"}')

    result = await classify_task_llm("resuma o contrato da Acme", ollama)

    assert result == ClassificationResult(category="summarize", target_hint="contrato da Acme")


@pytest.mark.asyncio
async def test_classify_task_llm_parses_json_with_null_target_hint() -> None:
    ollama = _ollama_returning('{"category": "list", "target_hint": null}')

    result = await classify_task_llm("liste os documentos", ollama)

    assert result == ClassificationResult(category="list", target_hint=None)


@pytest.mark.asyncio
async def test_classify_task_llm_extracts_json_from_surrounding_prose() -> None:
    ollama = _ollama_returning(
        'Claro, aqui está: {"category": "destructive", "target_hint": null} espero ajudar!'
    )

    result = await classify_task_llm("apaga tudo", ollama)

    assert result.category == "destructive"


@pytest.mark.asyncio
async def test_classify_task_llm_raises_on_malformed_json() -> None:
    ollama = _ollama_returning('{"category": "list", "target_hint": ')

    with pytest.raises(ClassificationError):
        await classify_task_llm("liste os documentos", ollama)


@pytest.mark.asyncio
async def test_classify_task_llm_raises_on_prose_without_json() -> None:
    ollama = _ollama_returning("Desculpe, não entendi bem a tarefa que você quer executar.")

    with pytest.raises(ClassificationError):
        await classify_task_llm("blah", ollama)


@pytest.mark.asyncio
async def test_classify_task_llm_raises_on_invalid_category() -> None:
    ollama = _ollama_returning('{"category": "delete_everything", "target_hint": null}')

    with pytest.raises(ClassificationError):
        await classify_task_llm("apaga tudo", ollama)


@pytest.mark.asyncio
async def test_classify_task_hybrid_uses_llm_result_when_valid() -> None:
    ollama = _ollama_returning('{"category": "list", "target_hint": null}')

    result = await classify_task_hybrid("mostra os documentos que eu tenho", ollama)

    assert result.category == "list"


@pytest.mark.asyncio
async def test_classify_task_hybrid_falls_back_on_malformed_json() -> None:
    ollama = _ollama_returning("isso não é json de jeito nenhum")

    result = await classify_task_hybrid("delete os documentos", ollama)

    assert result.category == "destructive"
    assert result.target_hint is None


@pytest.mark.asyncio
async def test_classify_task_hybrid_falls_back_on_invalid_category() -> None:
    ollama = _ollama_returning('{"category": "unknown", "target_hint": null}')

    result = await classify_task_hybrid("liste os documentos", ollama)

    assert result.category == "list"


@pytest.mark.asyncio
async def test_classify_task_hybrid_falls_back_when_chat_raises() -> None:
    ollama = AsyncMock(spec=OllamaClient)

    def _raise(*args: object, **kwargs: object) -> None:
        raise RuntimeError("connection refused")

    ollama.chat.side_effect = _raise

    result = await classify_task_hybrid("resuma o documento X", ollama)

    assert result.category == "summarize"
    assert result.target_hint is None


def test_resolve_target_document_exact_substring_match() -> None:
    documents = [
        {"id": "1", "filename": "contrato-acme.pdf"},
        {"id": "2", "filename": "manual-rh.pdf"},
    ]

    resolved = resolve_target_document("acme", documents)

    assert resolved is not None
    assert resolved["id"] == "1"


def test_resolve_target_document_fuzzy_match_tolerates_typo() -> None:
    documents = [{"id": "1", "filename": "relatorio-financeiro-2023.pdf"}]

    resolved = resolve_target_document("relatrio-financeiro-2023", documents)

    assert resolved is not None
    assert resolved["id"] == "1"


def test_resolve_target_document_no_match_returns_none() -> None:
    documents = [{"id": "1", "filename": "manual-rh.pdf"}]

    assert resolve_target_document("contrato completamente inexistente xyz", documents) is None


def test_resolve_target_document_ambiguous_multiple_matches_returns_none() -> None:
    documents = [
        {"id": "1", "filename": "contrato-acme-2023.pdf"},
        {"id": "2", "filename": "contrato-acme-2024.pdf"},
    ]

    assert resolve_target_document("contrato", documents) is None


def test_resolve_target_document_returns_none_without_hint() -> None:
    documents = [{"id": "1", "filename": "manual-rh.pdf"}]

    assert resolve_target_document(None, documents) is None


def test_resolve_target_document_returns_none_without_documents() -> None:
    assert resolve_target_document("qualquer coisa", []) is None
