"""Agentic task execution route.

Tasks run synchronously to completion (the graph itself caps iterations at
`settings.agent_max_iterations`, so a run is always bounded); the job_id
based GET endpoint lets the frontend poll a stable identifier even though
today's implementation resolves it immediately.
"""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agents.graph import run_agent_task
from api.deps import get_ollama_client
from core.ollama_client import OllamaClient

router = APIRouter(prefix="/api/agent", tags=["agent"])

# In-memory job store. Fine for a single-process local-first deployment;
# would move to the database if the app ever ran multi-process.
_jobs: dict[str, dict[str, Any]] = {}


class AgentTaskRequest(BaseModel):
    """Request body for POST /api/agent/task."""

    task: str


@router.post("/task")
async def submit_agent_task(
    request: AgentTaskRequest,
    ollama_client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> dict[str, str]:
    """Submit a task to the LangGraph agent and run it to completion.

    Args:
        request: `{"task": str}` — a natural-language task description.

    Returns:
        `{"job_id": str}` — use GET /api/agent/task/{job_id} to fetch the result.
    """
    job_id = str(uuid.uuid4())
    final_state = await run_agent_task(request.task, ollama_client=ollama_client)

    _jobs[job_id] = {
        "job_id": job_id,
        "status": final_state["status"],
        "result": final_state["result"],
        "iterations": final_state["iterations"],
        "tool_calls": final_state["tool_calls"],
    }

    return {"job_id": job_id}


@router.get("/task/{job_id}")
async def get_agent_task(job_id: str) -> dict[str, Any]:
    """Fetch the status and result of a previously submitted agent task.

    Args:
        job_id: The job identifier returned by POST /api/agent/task.

    Returns:
        `{"job_id", "status", "result", "iterations", "tool_calls"}`

    Raises:
        HTTPException 404: No task with this job_id was found.
    """
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    return job
