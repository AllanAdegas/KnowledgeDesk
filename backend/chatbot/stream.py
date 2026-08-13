"""SSE (Server-Sent Events) streaming for the chat endpoint."""

import json
from collections.abc import AsyncGenerator

from chatbot.session import add_message, get_history
from core.config import settings
from core.ollama_client import OllamaClient
from rag.pipeline import rag_query_stream


def _sse_event(data: dict[str, object]) -> str:
    """Format a dict as a single `text/event-stream` SSE data frame."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_chat_response(
    session_id: str,
    user_message: str,
    ollama_client: OllamaClient,
    rag_enabled: bool = False,
) -> AsyncGenerator[str, None]:
    """Stream the assistant's reply to `user_message` as SSE frames.

    Persists the user message immediately, streams tokens as they arrive
    (each as `{"type": "token", "content": str}`), then persists the full
    assistant reply and yields the terminal `{"type": "done", "session_id"}`
    event, per specs/chatbot.spec.md.

    When `rag_enabled` is True, the reply is grounded in indexed documents
    via the RAG pipeline instead of plain chat history.
    """
    await add_message(session_id, "user", user_message)

    full_reply_parts: list[str] = []

    if rag_enabled:
        async for token in rag_query_stream(user_message, ollama_client=ollama_client):
            full_reply_parts.append(token)
            yield _sse_event({"type": "token", "content": token})
    else:
        history = await get_history(session_id, limit=settings.max_history_turns)
        messages = [{"role": item["role"], "content": item["content"]} for item in history]
        messages.append({"role": "user", "content": user_message})

        async for token in ollama_client.chat(messages, stream=True):
            full_reply_parts.append(token)
            yield _sse_event({"type": "token", "content": token})

    full_reply = "".join(full_reply_parts)
    await add_message(session_id, "assistant", full_reply)

    yield _sse_event({"type": "done", "session_id": session_id})
