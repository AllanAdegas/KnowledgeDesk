"""Centralized application settings.

All configurable values (model names, chunking parameters, RAG thresholds,
history window size, etc.) live here so no module hardcodes "magic numbers".
Values can be overridden via environment variables or a `.env` file — see
`.env.example` at the backend root for the full list of supported keys.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration, loaded from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_request_timeout_seconds: float = 120.0

    # Storage
    chroma_persist_dir: str = "./data/chroma"
    database_url: str = "sqlite+aiosqlite:///./data/knowledgedesk.db"
    upload_dir: str = "./data/uploads"

    # Chat / history
    max_history_turns: int = 10

    # RAG
    rag_top_k: int = 5
    rag_score_threshold: float = 0.3
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    # Safe upper bound on how much extracted text is sent to the LLM when
    # generating the post-indexing summary, so a large document can't blow
    # past the local model's context window.
    rag_summary_max_chars: int = 6000

    # Agent
    agent_max_iterations: int = 5


settings = Settings()
