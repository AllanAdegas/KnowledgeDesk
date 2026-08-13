"""End-to-end RAG chain: retrieve relevant chunks, build a grounded prompt,
and stream the LLM's answer through the shared OllamaClient.
"""

from collections.abc import AsyncGenerator
from typing import Any

from core.ollama_client import OllamaClient
from core import ollama_client as ollama_client_module
from rag.retriever import RetrievedChunk, retrieve

NOT_FOUND_MESSAGE = "Não encontrei informações sobre isso nos documentos disponíveis."

_PROMPT_TEMPLATE = """Você é um assistente de conhecimento interno. \
Responda APENAS com base nos documentos fornecidos.
Se a informação não estiver nos documentos, diga explicitamente que não encontrou.

Documentos relevantes:
{context}

Pergunta: {query}"""


def build_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    """Build the grounded RAG prompt from the query and retrieved chunks."""
    context = "\n\n".join(chunk.text for chunk in chunks)
    return _PROMPT_TEMPLATE.format(context=context, query=query)


def _unique_sources(chunks: list[RetrievedChunk]) -> list[str]:
    seen: dict[str, None] = {}
    for chunk in chunks:
        filename = chunk.metadata.get("filename")
        if filename and filename not in seen:
            seen[filename] = None
    return list(seen.keys())


async def rag_query_stream(
    query: str,
    ollama_client: OllamaClient | None = None,
) -> AsyncGenerator[str, None]:
    """Stream the RAG answer for `query`, one text chunk at a time.

    If no relevant chunks clear the score threshold, yields the fixed
    "not found" message instead of calling the LLM, so the system never
    fabricates an answer with no grounding.
    """
    ollama = ollama_client or ollama_client_module.client
    chunks = await retrieve(query, ollama_client=ollama)

    if not chunks:
        yield NOT_FOUND_MESSAGE
        return

    prompt = build_prompt(query, chunks)
    async for token in ollama.chat([{"role": "user", "content": prompt}], stream=True):
        yield token

    sources = _unique_sources(chunks)
    if sources:
        yield f"\n\nFontes: {', '.join(sources)}"


async def rag_query(
    query: str,
    ollama_client: OllamaClient | None = None,
) -> dict[str, Any]:
    """Run the full RAG pipeline and return the aggregated answer with sources.

    Returns:
        `{"answer": str, "sources": list[str], "found": bool}`.
    """
    ollama = ollama_client or ollama_client_module.client
    chunks = await retrieve(query, ollama_client=ollama)

    if not chunks:
        return {"answer": NOT_FOUND_MESSAGE, "sources": [], "found": False}

    prompt = build_prompt(query, chunks)
    tokens = [
        token async for token in ollama.chat([{"role": "user", "content": prompt}], stream=True)
    ]
    answer = "".join(tokens)
    sources = _unique_sources(chunks)

    return {"answer": answer, "sources": sources, "found": True}
