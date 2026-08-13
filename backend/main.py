"""KnowledgeDesk FastAPI entry point.

Run locally with:

    uv run uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import documents, rag

app = FastAPI(
    title="KnowledgeDesk API",
    description=(
        "Local-first internal knowledge assistant: upload documents, chat with "
        "them via RAG, and run agentic tasks — all powered by a local Ollama "
        "instance, no data leaves the machine."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(rag.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe.

    Returns:
        A JSON object `{"status": "ok"}` when the API process is up.
    """
    return {"status": "ok"}
