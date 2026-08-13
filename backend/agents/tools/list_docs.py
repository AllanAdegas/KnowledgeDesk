"""Agent tool: list all documents currently indexed."""

from typing import Any

from rag.ingestion import list_indexed_documents


def list_docs() -> list[dict[str, Any]]:
    """Return every indexed document with its metadata.

    Returns:
        A list of `{"id": str, "filename": str, "chunks_count": int}`.
    """
    return list_indexed_documents()
