"""Vector similarity search over the documents ingested into ChromaDB."""

from dataclasses import dataclass
from typing import Any

from core.config import settings
from core.ollama_client import OllamaClient
from core.ollama_client import client as default_ollama_client
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
) -> list[RetrievedChunk]:
    """Return the top-k chunks most relevant to `query`, above the score threshold.

    Args:
        query: Natural language query to search for.
        k: Number of results to request (defaults to `settings.rag_top_k`).
        score_threshold: Minimum similarity score to keep a result (defaults
            to `settings.rag_score_threshold`).
        ollama_client: Optional injected client, primarily for tests.

    Returns:
        A list of `RetrievedChunk`, sorted by descending score. Empty if no
        chunk clears the threshold (including when the collection is empty).
    """
    ollama = ollama_client or default_ollama_client
    top_k = k or settings.rag_top_k
    threshold = score_threshold if score_threshold is not None else settings.rag_score_threshold

    collection = get_chroma_collection()
    if collection.count() == 0:
        return []

    query_embedding = await ollama.embed(query)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

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
