"""Chat routes: session creation, streamed messaging, and history retrieval."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.deps import get_ollama_client
from chatbot.session import create_session, get_history
from chatbot.stream import stream_chat_response
from core.ollama_client import OllamaClient

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/session")
async def create_chat_session() -> dict[str, str]:
    """Create a new chat session.

    Returns:
        `{"session_id": str}` — the history starts empty.
    """
    session_id = await create_session()
    return {"session_id": session_id}


class ChatMessageRequest(BaseModel):
    """Request body for POST /api/chat/message."""

    session_id: str
    message: str
    rag_enabled: bool = False


@router.post("/message")
async def send_chat_message(
    request: ChatMessageRequest,
    ollama_client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> StreamingResponse:
    """Send a message and stream the assistant's reply over SSE.

    The last `max_history_turns` messages are included as context. Each
    streamed frame is `data: {"type": "token", "content": str}\\n\\n`,
    followed by a terminal `data: {"type": "done", "session_id": str}\\n\\n`.

    Args:
        request: `{"session_id": str, "message": str, "rag_enabled": bool}`.

    Returns:
        A `text/event-stream` response.
    """
    generator = stream_chat_response(
        request.session_id,
        request.message,
        ollama_client=ollama_client,
        rag_enabled=request.rag_enabled,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str) -> list[dict[str, str]]:
    """Return the stored message history for a session.

    Args:
        session_id: The session's UUID.

    Returns:
        A list of `{"role": str, "content": str}`, oldest first.
    """
    return await get_history(session_id, limit=None)
