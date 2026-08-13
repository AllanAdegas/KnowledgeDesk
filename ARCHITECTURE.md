# ARCHITECTURE

## Visão geral

KnowledgeDesk é um monorepo com três partes independentes que conversam por
HTTP: um backend FastAPI (Python, assíncrono), um frontend React/Vite
(TypeScript) e uma suíte de testes E2E (Playwright) separada de ambos.
Tudo roda local: o único serviço externo ao processo é o Ollama (LLM +
embeddings) e, opcionalmente, um ChromaDB standalone via Docker Compose.

```
knowledgedesk/
├── specs/          # Spec Driven Development — comportamento antes do código
├── backend/        # FastAPI + LangChain + LangGraph + ChromaDB + SQLite
├── frontend/       # React 18 + Vite + TypeScript + TailwindCSS
├── e2e/            # Playwright, roda contra o stack real + Ollama real
└── .github/        # CI: lint + test + build
```

## Backend

### Camadas

```
api/routes/*  → chatbot/ , rag/ , agents/   → core/ollama_client.py → Ollama
                        │
                        ▼
              core/database.py (SQLite)   rag/ingestion.py (ChromaDB)
```

- **`core/config.py`**: única fonte de verdade para todo valor configurável
  (modelos, chunk size/overlap, top_k, score threshold, janela de histórico,
  cap de iterações do agente). Nada é hardcoded em outro módulo.
- **`core/ollama_client.py`**: único ponto de contato com Ollama (HTTP via
  `httpx.AsyncClient`). Todo o resto do backend depende dele por injeção
  (`ollama_client: OllamaClient | None = None`), nunca abre sua própria
  conexão HTTP — é essa costura que permite mockar 100% dos testes
  automatizados sem tocar em uma instância real.
- **`rag/`**: ingestão (extração + chunking + embeddings + persistência em
  Chroma), retriever (busca vetorial com filtro por score) e pipeline
  (monta o prompt grounded e stream a resposta).
- **`chatbot/`**: sessões e histórico em SQLite (via SQLAlchemy async +
  aiosqlite) e o streaming SSE que persiste a conversa incrementalmente.
- **`agents/`**: state machine LangGraph (`clarify → plan → execute_tools →
  respond`, com loop `execute_tools ↔ plan` até o cap de iterações) e três
  tools de só-leitura (`search_docs`, `list_docs`, `summarize`).

### Decisões técnicas

**SQLite (sessões) + ChromaDB (vetores), duas lojas separadas.** Sessões de
chat são dados relacionais simples (sequência de mensagens por sessão) —
SQLite via SQLAlchemy async é suficiente e evita a complexidade de rodar
Postgres localmente. Embeddings de documentos precisam de busca por
similaridade vetorial, que o Chroma faz nativamente; forçar isso dentro do
SQLite (ou vice-versa, texto de chat dentro do Chroma) misturaria dois
modelos de acesso muito diferentes só para "ter um banco só".

**SSE em vez de WebSocket para o streaming do chat.** O fluxo é
unidirecional (cliente manda uma mensagem, servidor stream a resposta) —
WebSocket adicionaria complexidade de gerência de conexão bidirecional sem
nenhum ganho aqui. `text/event-stream` também é trivialmente consumível por
`fetch` + `ReadableStream` no frontend, sem biblioteca extra.

**Roteamento do agente por heurística de palavras-chave, não por LLM.**
Classificar a intenção da tarefa (`destructive` / `list` / `summarize` /
`ambiguous`) via chamada ao LLM tornaria os testes não-determinísticos (ou
exigiria mockar uma "opinião" do modelo, o que é frágil). A classificação
determinística mantém o roteamento 100% testável e reserva a chamada real ao
LLM para a etapa que de fato precisa dele: a sumarização.

**Máquina de estados do agente com cap de iterações vindo do config.** O
grafo LangGraph tem 4 nós — `clarify`, `plan`, `execute_tools`, `respond` —
e um loop `execute_tools → plan` para tarefas que não convergem de primeira
(ex.: `summarize` sem chunks relevantes). O cap (`agent_max_iterations`,
padrão 5) é checado dentro do próprio nó `execute_tools`, nunca na função de
roteamento condicional — LangGraph só persiste mutações de estado feitas
dentro de nós, não dentro de callbacks de roteamento.

**`OllamaClient` resolvido em tempo de chamada, não capturado no import.**
Vários módulos inicialmente faziam `from core.ollama_client import client as
default_ollama_client` no topo do arquivo — isso captura o objeto por valor
no momento do import, então `monkeypatch.setattr("core.ollama_client.client",
mock)` nos testes nunca alcançava esses módulos. A correção foi importar o
*módulo* (`from core import ollama_client as ollama_client_module`) e
resolver `.client` dentro de cada função, no momento da chamada.

## Frontend

```
pages/       (ChatPage, DocumentsPage, AgentPage)   — "burras", só compõem
   │
hooks/       (useChat, useDocuments, useAgent)      — toda lógica de fetch/estado
   │
api/client.ts — axios + streamChatMessage (fetch + ReadableStream para SSE)
```

Hooks isolam toda a lógica assíncrona (chamadas HTTP, streaming, polling)
das páginas, que ficam apenas responsáveis por renderizar o estado exposto
pelo hook — isso é o que torna os componentes testáveis com React Testing
Library sem precisar montar a árvore de fetch inteira.

`EventSource` foi descartado para o chat porque só suporta requisições GET;
o endpoint de mensagem é um POST (precisa enviar `session_id` + `message` no
corpo), então o streaming é feito manualmente com `fetch` +
`response.body.getReader()`, parseando frames `data: {...}\n\n` à mão.

## Testes

- **Backend**: pytest + pytest-asyncio, `mock_ollama` (fixture global em
  `conftest.py`) substitui `core.ollama_client.client` por um `AsyncMock` —
  nenhum teste toca a rede. SQLite e Chroma são redirecionados para
  diretórios `tmp_path` por teste, isolando estado entre execuções.
- **Frontend**: Vitest + React Testing Library, com `vi.spyOn` sobre os
  módulos de `src/api/client.ts` para simular respostas do backend
  (incluindo o parsing de frames SSE sobre um `ReadableStream` real de
  teste).
- **E2E**: Playwright, roda contra o stack real (frontend + backend +
  Ollama real) — não mockado, não executado nesta sessão por falta dos
  modelos `llama3.2`/`nomic-embed-text` no ambiente local.
