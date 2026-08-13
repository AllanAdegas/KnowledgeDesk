"""Agent tool: search indexed documents for content relevant to a query."""

from typing import Any

from core.ollama_client import OllamaClient
from rag.retriever import retrieve


async def search_docs(
    query: str,
    ollama_client: OllamaClient | None = None,
    filename: str | None = None,
) -> list[dict[str, Any]]:
    """Search the indexed documents for chunks relevant to `query`.

    Thin adapter over `rag.retriever.retrieve` shaped for agent tool-calling
    (plain dicts instead of the `RetrievedChunk` dataclass).

    Args:
        query: Natural language query to search for.
        ollama_client: Optional injected client, primarily for tests.
        filename: Optional filename filter, forwarded to `retrieve()` — when
            set, restricts the search to chunks from that document only.

    Returns:
        A list of `{"text": str, "score": float, "filename": str | None}`.
    """
    chunks = await retrieve(query, ollama_client=ollama_client, filename=filename)
    return [
        {"text": chunk.text, "score": chunk.score, "filename": chunk.metadata.get("filename")}
        for chunk in chunks
    ]
