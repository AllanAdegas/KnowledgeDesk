"""Document upload, listing, and deletion routes."""

import tempfile
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from api.deps import get_ollama_client
from core.ollama_client import OllamaClient
from rag.ingestion import (
    DocumentExtractionError,
    UnsupportedFileTypeError,
    get_chroma_collection,
    ingest_document,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile,
    ollama_client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> dict[str, Any]:
    """Upload and index a document (PDF, DOCX or TXT).

    Extracts the document's text, splits it into chunks, embeds each chunk
    and persists it to the vector store.

    Args:
        file: The uploaded file (multipart/form-data).

    Returns:
        `{"id": str, "filename": str, "chunks_count": int, "status": "indexed"}`

    Raises:
        HTTPException 422: The file extension is not supported.
        HTTPException 400: The file's text could not be extracted (corrupted/empty).
    """
    filename = file.filename or "upload"
    suffix = Path(filename).suffix

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name

    try:
        result = await ingest_document(tmp_path, filename, ollama_client=ollama_client)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DocumentExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return result


@router.get("")
async def list_documents() -> list[dict[str, Any]]:
    """List all indexed documents with their chunk counts.

    Returns:
        A list of `{"id": str, "filename": str, "chunks_count": int}`.
    """
    collection = get_chroma_collection()
    all_chunks = collection.get(include=["metadatas"])
    metadatas = all_chunks.get("metadatas") or []

    documents: dict[str, dict[str, Any]] = {}
    for metadata in metadatas:
        document_id = metadata.get("document_id")
        if not document_id:
            continue
        if document_id not in documents:
            documents[document_id] = {
                "id": document_id,
                "filename": metadata.get("filename"),
                "chunks_count": 0,
            }
        documents[document_id]["chunks_count"] += 1

    return list(documents.values())


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> dict[str, str]:
    """Delete a document and all its chunks from the vector store.

    Args:
        document_id: The document's UUID, as returned by the upload route.

    Returns:
        `{"id": document_id, "status": "deleted"}`
    """
    collection = get_chroma_collection()
    collection.delete(where={"document_id": document_id})
    return {"id": document_id, "status": "deleted"}
