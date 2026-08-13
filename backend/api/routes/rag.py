"""Pure RAG query route (no chat history involved)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.deps import get_ollama_client
from core.ollama_client import OllamaClient
from rag.pipeline import rag_query

router = APIRouter(prefix="/api/rag", tags=["rag"])


class RagQueryRequest(BaseModel):
    """Request body for POST /api/rag/query."""

    query: str


@router.post("/query")
async def query_rag(
    request: RagQueryRequest,
    ollama_client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> dict[str, Any]:
    """Answer a question using only the indexed documents as context.

    Retrieves the most relevant chunks, injects them into the prompt, and
    returns the LLM's answer together with the cited source filenames. If no
    chunk clears the relevance threshold, returns a fixed "not found" answer
    instead of letting the model improvise.

    Args:
        request: `{"query": str}`.

    Returns:
        `{"answer": str, "sources": list[str], "found": bool}`
    """
    return await rag_query(request.query, ollama_client=ollama_client)
