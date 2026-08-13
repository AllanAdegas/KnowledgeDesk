"""Shared FastAPI dependencies."""

from core.ollama_client import OllamaClient
from core import ollama_client as ollama_client_module


def get_ollama_client() -> OllamaClient:
    """Provide the shared OllamaClient instance to route handlers.

    Routes depend on this instead of importing the module-level singleton
    directly, keeping the FastAPI dependency-injection graph explicit and
    easy to override in tests if ever needed.
    """
    return ollama_client_module.client
