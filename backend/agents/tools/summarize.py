"""Agent tool: summarize a piece of text using the LLM."""

from core import ollama_client as ollama_client_module
from core.ollama_client import OllamaClient

_SUMMARY_PROMPT_TEMPLATE = (
    "Resuma o texto a seguir em português, de forma objetiva e estruturada em "
    "tópicos com os pontos principais:\n\n{text}"
)


async def summarize(text: str, ollama_client: OllamaClient | None = None) -> str:
    """Summarize `text` into key points using the chat model.

    Args:
        text: The text to summarize (e.g. concatenated document chunks).
        ollama_client: Optional injected client, primarily for tests.

    Returns:
        The model's summary, as a single string.
    """
    ollama = ollama_client or ollama_client_module.client
    prompt = _SUMMARY_PROMPT_TEMPLATE.format(text=text)
    tokens = [
        token async for token in ollama.chat([{"role": "user", "content": prompt}], stream=True)
    ]
    return "".join(tokens)
