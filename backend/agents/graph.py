"""LangGraph state machine for agentic task execution.

Flow: [START] -> clarify? -> plan -> execute_tools -> respond -> [END],
looping back from execute_tools to plan (up to `settings.agent_max_iterations`
times) whenever a tool call doesn't yet produce a usable result — this is
how the "para após N iterações" behavior from specs/agent.spec.md is
implemented.

Task classification (which tool to use, whether it's ambiguous or
destructive) is done with lightweight keyword heuristics rather than an LLM
call: it needs to be deterministic so it can be exercised by fully-mocked
tests, and the local models available (llama3.2/mistral) are not reliable
enough at structured intent classification to be worth the extra latency
here. The LLM (via OllamaClient) is still used for the actual generative
work — summarization.
"""

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


class AgentState(TypedDict):
    """State threaded through every node of the agent graph."""

    task: str
    messages: list[dict[str, str]]
    tool_calls: list[dict[str, str]]
    iterations: int
    result: str | None
    status: str


def classify_task(task: str) -> str:
    """Classify a task into one of: destructive, list, summarize, ambiguous."""
    lowered = task.lower()
    if any(keyword in lowered for keyword in DESTRUCTIVE_KEYWORDS):
        return "destructive"
    if any(keyword in lowered for keyword in LIST_KEYWORDS):
        return "list"
    if any(keyword in lowered for keyword in SUMMARIZE_KEYWORDS):
        return "summarize"
    return "ambiguous"


def _format_doc_list(docs: list[dict[str, Any]]) -> str:
    if not docs:
        return "Nenhum documento indexado no momento."
    lines = [f"- {doc['filename']} ({doc['chunks_count']} trechos indexados)" for doc in docs]
    return "Documentos disponíveis:\n" + "\n".join(lines)


async def clarify_node(state: AgentState) -> AgentState:
    """Ask for clarification up front if the task doesn't map to a known action."""
    if classify_task(state["task"]) == "ambiguous":
        state["status"] = "needs_clarification"
        state["result"] = (
            "Sua tarefa não ficou clara. Pode detalhar quais documentos ou qual "
            "ação específica você quer? (ex: 'liste documentos sobre RH' ou "
            "'resuma o documento X')"
        )
    return state


def route_after_clarify(state: AgentState) -> str:
    return "respond" if state["status"] == "needs_clarification" else "plan"


async def plan_node(state: AgentState) -> AgentState:
    """Pick which tool to use for this task/iteration."""
    category = classify_task(state["task"])
    state["tool_calls"].append({"tool": category})
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
            chunks = await search_docs(state["task"], ollama_client=ollama_client)
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

    graph.add_node("clarify", clarify_node)
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
    }

    final_state: AgentState = await compiled_graph.ainvoke(initial_state)
    return final_state
