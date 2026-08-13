"""Vector similarity search over the documents ingested into ChromaDB."""

from dataclasses import dataclass
from typing import Any

from core.config import settings
from core.ollama_client import OllamaClient
from core import ollama_client as ollama_client_module
from rag.ingestion import get_chroma_collection


@dataclass(frozen=True)
class RetrievedChunk:
    """A single chunk returned by the retriever, with its similarity score."""

    text: str
    score: float
    metadata: dict[str, Any]


def _distance_to_similarity(distance: float) -> float:
    """Convert a Chroma L2/cosine distance into a 0..1 similarity score.

    Chroma's default space returns a distance where 0 means identical.
    We convert it into a similarity score via `1 / (1 + distance)` so it
    behaves consistently for thresholding regardless of the exact metric.
    """
    return 1.0 / (1.0 + max(distance, 0.0))


async def retrieve(
    query: str,
    k: int | None = None,
    score_threshold: float | None = None,
    ollama_client: OllamaClient | None = None,
    filename: str | None = None,
) -> list[RetrievedChunk]:
    """Return the top-k chunks most relevant to `query`, above the score threshold.

    Args:
        query: Natural language query to search for.
        k: Number of results to request (defaults to `settings.rag_top_k`).
        score_threshold: Minimum similarity score to keep a result (defaults
            to `settings.rag_score_threshold`).
        ollama_client: Optional injected client, primarily for tests.
        filename: Optional filename filter — when set, only chunks whose
            `filename` metadata matches exactly are considered (used by the
            agent when a natural-language task resolves to a specific
            indexed document). When omitted, behaves exactly like before,
            searching the whole corpus.

    Returns:
        A list of `RetrievedChunk`, sorted by descending score. Empty if no
        chunk clears the threshold (including when the collection is empty).
    """
    ollama = ollama_client or ollama_client_module.client
    top_k = k or settings.rag_top_k
    threshold = score_threshold if score_threshold is not None else settings.rag_score_threshold

    collection = get_chroma_collection()
    if collection.count() == 0:
        return []

    query_embedding = await ollama.embed(query)
    query_kwargs: dict[str, Any] = {"query_embeddings": [query_embedding], "n_results": top_k}
    if filename:
        query_kwargs["where"] = {"filename": filename}
    results = collection.query(**query_kwargs)

    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    chunks: list[RetrievedChunk] = []
    for text, metadata, distance in zip(documents, metadatas, distances, strict=False):
        score = _distance_to_similarity(distance)
        if score >= threshold:
            chunks.append(RetrievedChunk(text=text, score=score, metadata=metadata or {}))

    chunks.sort(key=lambda chunk: chunk.score, reverse=True)
    return chunks
