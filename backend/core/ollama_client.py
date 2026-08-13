"""Thin async wrapper around the Ollama HTTP API.

`OllamaClient` is the *only* point of contact with Ollama in the whole
codebase. Every other module (ingestion, retriever, pipeline, chat, agent
tools) depends on an `OllamaClient` instance injected at call time rather
than talking HTTP directly. That single seam is what lets every automated
test (unit, integration, component) mock Ollama entirely — no test in this
repository ever performs a real network call to a running Ollama server.
"""

from collections.abc import AsyncGenerator
from typing import Any, TypedDict

import httpx

from core.config import settings


class ChatMessage(TypedDict):
    """A single message in an Ollama chat conversation."""

    role: str
    content: str


class OllamaClient:
    """Async client for the subset of the Ollama HTTP API this app needs."""

    def __init__(
        self,
        base_url: str | None = None,
        chat_model: str | None = None,
        embed_model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = base_url or settings.ollama_base_url
        self.chat_model = chat_model or settings.ollama_chat_model
        self.embed_model = embed_model or settings.ollama_embed_model
        self.timeout = timeout or settings.ollama_request_timeout_seconds

    async def chat(
        self, messages: list[ChatMessage], stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """Send a chat completion request and yield response text chunks.

        When `stream` is True (the default), each yielded string is one
        incremental token/chunk as produced by Ollama. When False, a single
        chunk containing the full response is yielded.
        """
        payload: dict[str, Any] = {
            "model": self.chat_model,
            "messages": messages,
            "stream": stream,
        }

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as http_client:
            if not stream:
                response = await http_client.post("/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                yield data.get("message", {}).get("content", "")
                return

            async with http_client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    chunk = httpx.Response(200, content=line).json()
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if chunk.get("done"):
                        break

    async def embed(self, text: str) -> list[float]:
        """Return the embedding vector for `text` using the embedding model."""
        payload = {"model": self.embed_model, "prompt": text}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as http_client:
            response = await http_client.post("/api/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()
            embedding: list[float] = data.get("embedding", [])
            return embedding

    async def list_models(self) -> list[str]:
        """Return the names of models currently available in the local Ollama."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as http_client:
            response = await http_client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            models: list[dict[str, Any]] = data.get("models", [])
            return [model["name"] for model in models]


client = OllamaClient()
"""Module-level singleton used by the rest of the app; tests monkeypatch this."""
