"""LangGraph state machine for agentic task execution.

Flow: [START] -> clarify -> plan -> execute_tools -> respond -> [END],
looping back from execute_tools to plan (up to `settings.agent_max_iterations`
times) whenever a tool call doesn't yet produce a usable result — this is
how the "para após N iterações" behavior from specs/agent.spec.md is
implemented.

Task classification (which tool to use, whether it's ambiguous or
destructive) is done with a **hybrid** strategy: the LLM (via `OllamaClient`,
`stream=False`) is asked to return structured JSON
(`{"category": ..., "target_hint": ...}`) first; if that response is
missing, isn't valid JSON, or names a category outside the expected enum,
classification falls back to the deterministic keyword heuristic in
`classify_task()`. This keeps the system testable/deterministic (every
automated test mocks `ollama_client.chat` and can exercise both the
happy path and the fallback path) while giving the agent real natural
language understanding when the local model cooperates — Paranoia
Pragmática: never trust the local LLM's structured output blindly.
"""

import difflib
import json
import re
from dataclasses import dataclass
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agents.tools.list_docs import list_docs
from agents.tools.search_docs import search_docs
from agents.tools.summarize import summarize
from core import ollama_client as ollama_client_module
from core.config import settings
from core.ollama_client import OllamaClient

DESTRUCTIVE_KEYWORDS = ("delete", "deletar", "apague", "apagar", "remova", "remover", "exclua", "excluir")
LIST_KEYWORDS = ("liste", "listar", "list")
SUMMARIZE_KEYWORDS = ("resum",)

VALID_CATEGORIES = {"destructive", "list", "summarize", "ambiguous"}

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

_CLASSIFICATION_PROMPT_TEMPLATE = (
    "Classifique a tarefa do usuário em exatamente uma destas categorias:\n"
    "- destructive: pede para apagar/deletar/remover documentos\n"
    "- list: pede para listar/mostrar os documentos indexados\n"
    "- summarize: pede um resumo ou os pontos principais de um documento\n"
    "- ambiguous: não se encaixa claramente em nenhuma das anteriores\n\n"
    "Se a tarefa mencionar um documento específico (por nome, assunto ou "
    "apelido), extraia esse trecho livre em 'target_hint'; caso contrário "
    "'target_hint' deve ser null.\n\n"
    "Responda APENAS com um JSON no formato exato, sem texto adicional:\n"
    '{{"category": "<categoria>", "target_hint": "<trecho ou null>"}}\n\n'
    "Tarefa: {task}"
)


class ClassificationError(Exception):
    """Raised internally when the LLM's classification can't be trusted."""


@dataclass(frozen=True)
class ClassificationResult:
    """Result of classifying a task, whether from the LLM or the fallback."""

    category: str
    target_hint: str | None = None


class AgentState(TypedDict):
    """State threaded through every node of the agent graph."""

    task: str
    messages: list[dict[str, str]]
    tool_calls: list[dict[str, str]]
    iterations: int
    result: str | None
    status: str
    task_category: str
    target_document_id: str | None
    target_filename: str | None


def classify_task(task: str) -> str:
    """Classify a task into one of: destructive, list, summarize, ambiguous.

    Deterministic keyword heuristic — used directly by tests, and as the
    fallback for `classify_task_llm` when the LLM's output can't be trusted.
    """
    lowered = task.lower()
    if any(keyword in lowered for keyword in DESTRUCTIVE_KEYWORDS):
        return "destructive"
    if any(keyword in lowered for keyword in LIST_KEYWORDS):
        return "list"
    if any(keyword in lowered for keyword in SUMMARIZE_KEYWORDS):
        return "summarize"
    return "ambiguous"


async def classify_task_llm(task: str, ollama_client: OllamaClient) -> ClassificationResult:
    """Classify a task using the LLM, asking for structured JSON output.

    Args:
        task: The natural-language task description.
        ollama_client: The client to call (`stream=False`, single-shot).

    Returns:
        A `ClassificationResult` with a valid category and optional
        `target_hint` (the free-text document reference, if any).

    Raises:
        ClassificationError: If the LLM's response is missing, not valid
            JSON, or names a category outside the expected enum. Callers
            are expected to catch this and fall back to `classify_task`.
    """
    prompt = _CLASSIFICATION_PROMPT_TEMPLATE.format(task=task)
    tokens = [
        token
        async for token in ollama_client.chat([{"role": "user", "content": prompt}], stream=False)
    ]
    raw = "".join(tokens).strip()

    match = _JSON_BLOCK_RE.search(raw)
    if not match:
        raise ClassificationError(f"No JSON object found in LLM response: {raw!r}")

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ClassificationError(f"Malformed JSON from LLM: {raw!r}") from exc

    if not isinstance(parsed, dict):
        raise ClassificationError(f"LLM JSON was not an object: {raw!r}")

    category = parsed.get("category")
    if category not in VALID_CATEGORIES:
        raise ClassificationError(f"Invalid category from LLM: {category!r}")

    target_hint = parsed.get("target_hint")
    if not isinstance(target_hint, str) or not target_hint.strip():
        target_hint = None

    return ClassificationResult(category=category, target_hint=target_hint)


async def classify_task_hybrid(task: str, ollama_client: OllamaClient) -> ClassificationResult:
    """Classify a task via the LLM, falling back to the keyword heuristic.

    This is the single entry point the graph uses: it tries
    `classify_task_llm` first and, on any failure (bad/missing JSON,
    invalid category, or the underlying call raising for any reason —
    e.g. the LLM being unreachable), degrades to `classify_task` with no
    target hint, matching this project's "never trust the local LLM
    blindly" policy.
    """
    try:
        return await classify_task_llm(task, ollama_client)
    except Exception:  # noqa: BLE001 - any failure degrades to the deterministic fallback
        return ClassificationResult(category=classify_task(task), target_hint=None)


def resolve_target_document(
    target_hint: str | None, documents: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Resolve a free-text document reference against the indexed documents.

    Matches `target_hint` against each document's `filename` via
    case-insensitive substring matching (in both directions) and, failing
    that, fuzzy matching (`difflib.get_close_matches`) to tolerate typos.

    Args:
        target_hint: Free text extracted by the LLM (e.g. "contrato da Acme").
        documents: Indexed documents, each with at least an `id`/`filename`.

    Returns:
        The single matching document dict, or `None` if there's no match
        or more than one plausible match (degrades safely rather than
        guessing).
    """
    if not target_hint or not documents:
        return None

    hint = target_hint.strip().lower()
    if not hint:
        return None

    substring_matches = [
        doc
        for doc in documents
        if hint in doc["filename"].lower() or doc["filename"].lower() in hint
    ]
    if len(substring_matches) == 1:
        return substring_matches[0]
    if len(substring_matches) > 1:
        return None

    filenames = [doc["filename"] for doc in documents]
    close_matches = difflib.get_close_matches(target_hint, filenames, n=2, cutoff=0.6)
    if len(close_matches) == 1:
        return next(doc for doc in documents if doc["filename"] == close_matches[0])

    return None


def _format_doc_list(docs: list[dict[str, Any]]) -> str:
    if not docs:
        return "Nenhum documento indexado no momento."
    lines = [f"- {doc['filename']} ({doc['chunks_count']} trechos indexados)" for doc in docs]
    return "Documentos disponíveis:\n" + "\n".join(lines)


def make_clarify_node(ollama_client: OllamaClient):
    """Build the clarify node, closing over the OllamaClient used to classify.

    Runs the hybrid classification exactly once per task and stores the
    result in `AgentState` (`task_category`, `target_document_id`,
    `target_filename`) so `plan_node` doesn't need to reclassify on every
    loop iteration. Asks for clarification up front when the task is
    ambiguous, or when it names a target document that can't be resolved
    against the indexed documents.
    """

    async def clarify_node(state: AgentState) -> AgentState:
        classification = await classify_task_hybrid(state["task"], ollama_client)
        state["task_category"] = classification.category
        state["target_document_id"] = None
        state["target_filename"] = None

        if classification.category == "ambiguous":
            state["status"] = "needs_clarification"
            state["result"] = (
                "Sua tarefa não ficou clara. Pode detalhar quais documentos ou qual "
                "ação específica você quer? (ex: 'liste documentos sobre RH' ou "
                "'resuma o documento X')"
            )
            return state

        if classification.target_hint:
            documents = list_docs()
            resolved = resolve_target_document(classification.target_hint, documents)
            if resolved is not None:
                state["target_document_id"] = resolved["id"]
                state["target_filename"] = resolved["filename"]
            else:
                state["status"] = "needs_clarification"
                state["result"] = (
                    f"Não encontrei nenhum documento indexado correspondente a "
                    f"'{classification.target_hint}'. " + _format_doc_list(documents)
                )
                return state

        return state

    return clarify_node


def route_after_clarify(state: AgentState) -> str:
    return "respond" if state["status"] == "needs_clarification" else "plan"


async def plan_node(state: AgentState) -> AgentState:
    """Pick which tool to use for this task/iteration.

    Classification already happened once in `clarify_node`; this just
    reads the decision instead of reclassifying on every loop iteration.
    """
    state["tool_calls"].append({"tool": state["task_category"]})
    return state


def make_execute_tools_node(ollama_client: OllamaClient):
    """Build the execute_tools node, closing over the OllamaClient to use."""

    async def execute_tools_node(state: AgentState) -> AgentState:
        category = state["tool_calls"][-1]["tool"]
        state["iterations"] += 1

        if category == "destructive":
            state["status"] = "refused"
            state["result"] = (
                "Não posso executar essa ação: tenho apenas permissão de leitura "
                "sobre os documentos indexados, não de escrita/exclusão."
            )
        elif category == "list":
            docs = list_docs()
            state["result"] = _format_doc_list(docs)
            state["status"] = "done"
        elif category == "summarize":
            chunks = await search_docs(
                state["task"],
                ollama_client=ollama_client,
                filename=state.get("target_filename"),
            )
            if not chunks:
                state["status"] = "pending"
            else:
                joined_text = "\n\n".join(chunk["text"] for chunk in chunks)
                state["result"] = await summarize(joined_text, ollama_client=ollama_client)
                state["status"] = "done"
        else:
            state["status"] = "pending"

        # Node functions are the only place LangGraph reliably persists state
        # mutations (conditional-edge routing functions must stay read-only),
        # so the max-iterations finalization happens here rather than in the
        # router below.
        if state["status"] == "pending" and state["iterations"] >= settings.agent_max_iterations:
            state["status"] = "max_iterations_reached"
            state["result"] = state["result"] or (
                "Não consegui completar a tarefa dentro do limite de iterações "
                f"({settings.agent_max_iterations}). Progresso parcial: nenhum "
                "resultado definitivo foi encontrado nos documentos indexados."
            )

        return state

    return execute_tools_node


def route_after_execute(state: AgentState) -> str:
    if state["status"] == "pending":
        return "plan"
    return "respond"


async def respond_node(state: AgentState) -> AgentState:
    """Terminal node — state is already fully populated by this point."""
    return state


def build_agent_graph(ollama_client: OllamaClient | None = None) -> Any:
    """Compile the LangGraph state machine, ready to `.ainvoke(state)`."""
    client = ollama_client or ollama_client_module.client
    graph = StateGraph(AgentState)

    graph.add_node("clarify", make_clarify_node(client))
    graph.add_node("plan", plan_node)
    graph.add_node("execute_tools", make_execute_tools_node(client))
    graph.add_node("respond", respond_node)

    graph.set_entry_point("clarify")
    graph.add_conditional_edges("clarify", route_after_clarify, {"respond": "respond", "plan": "plan"})
    graph.add_edge("plan", "execute_tools")
    graph.add_conditional_edges(
        "execute_tools", route_after_execute, {"respond": "respond", "plan": "plan"}
    )
    graph.add_edge("respond", END)

    return graph.compile()


async def run_agent_task(task: str, ollama_client: OllamaClient | None = None) -> AgentState:
    """Run a task through the agent graph to completion and return its final state."""
    client = ollama_client or ollama_client_module.client
    compiled_graph = build_agent_graph(ollama_client=client)

    initial_state: AgentState = {
        "task": task,
        "messages": [],
        "tool_calls": [],
        "iterations": 0,
        "result": None,
        "status": "pending",
        "task_category": "",
        "target_document_id": None,
        "target_filename": None,
    }

    final_state: AgentState = await compiled_graph.ainvoke(initial_state)
    return final_state
