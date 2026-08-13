# KnowledgeDesk

## Demo

> No GIF is included in this session — recording one requires a real Ollama
> instance with `llama3.2` and `nomic-embed-text` pulled, neither of which is
> available in this environment (only `qwen3` is installed). Once those
> models are pulled and the app is running locally, record a GIF that shows:
>
> 1. Dragging a PDF onto the upload zone and watching it flip to "indexado".
> 2. Toggling RAG on in the chat sidebar.
> 3. Asking a question about the uploaded document and watching the answer
>    stream in token by token, ending with a cited source.
>
> Save it as `docs/demo.gif` and reference it here: `![demo](docs/demo.gif)`.

## O que é

KnowledgeDesk é um assistente de conhecimento interno que roda 100% local
via Ollama: qualquer empresa faz upload de PDFs/DOCX/TXT e conversa com eles
em linguagem natural, sem que nenhum dado saia da máquina. Além do chat com
RAG, o sistema inclui um agente (LangGraph) capaz de listar, buscar e
resumir documentos de forma autônoma, dentro de limites de segurança
explícitos (somente leitura, número máximo de iterações).

## Arquitetura

```
┌─────────────┐      HTTP/SSE      ┌──────────────┐      HTTP       ┌────────┐
│   Frontend   │ ─────────────────▶ │   Backend    │ ──────────────▶ │ Ollama │
│ React + Vite │ ◀───────────────── │   FastAPI    │ ◀────────────── │ (local)│
└─────────────┘                     └──────┬───────┘                 └────────┘
                                            │
                        ┌───────────────────┼───────────────────┐
                        ▼                   ▼                   ▼
                 ┌─────────────┐    ┌───────────────┐    ┌─────────────┐
                 │  ChromaDB   │    │    SQLite     │    │  LangGraph  │
                 │  (vectors)  │    │  (sessions)   │    │   (agent)   │
                 └─────────────┘    └───────────────┘    └─────────────┘
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the module-by-module breakdown
and the key technical decisions (why SQLite + Chroma instead of one store,
why SSE instead of WebSockets, how the LangGraph state machine is shaped).

## Stack

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C)
![ChromaDB](https://img.shields.io/badge/ChromaDB-vector%20store-orange)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6?logo=typescript&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-06B6D4?logo=tailwindcss&logoColor=white)
![Pytest](https://img.shields.io/badge/pytest-passing-0A9EDC?logo=pytest&logoColor=white)
![Vitest](https://img.shields.io/badge/vitest-passing-6E9F18?logo=vitest&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-E2E-2EAD33?logo=playwright&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-000000)

## Como rodar

```bash
# 1. Instale os modelos necessários no Ollama (uma vez)
ollama pull llama3.2 && ollama pull nomic-embed-text

# 2. Backend
cd backend && uv sync && cp .env.example .env && uv run uvicorn main:app --reload

# 3. Frontend (em outro terminal)
cd frontend && npm install && cp .env.example .env && npm run dev

# 4. Acesse
open http://localhost:5173
```

Alternativamente, com Docker: `docker compose up` (requer Ollama rodando no
host — veja `OLLAMA_BASE_URL` em `docker-compose.yml`).

## Metodologia

Este projeto seguiu **Spec Driven Development**: antes de qualquer código,
os comportamentos esperados de cada módulo (RAG, chatbot, agente,
fine-tuning) foram escritos em linguagem clara (estilo DADO/QUANDO/ENTÃO)
em [`specs/`](specs/). Cada spec guiou diretamente a suíte de testes —
`rag.spec.md` → `test_rag_api.py`, `agent.spec.md` → `test_agent_tools.py`
e `test_agent_api.py`, e assim por diante. O histórico de commits reflete
esse fluxo: `spec:` sempre antes do `feat:` correspondente, e `test:` logo
em seguida, nunca pulando etapas. Todo teste automatizado mocka o Ollama —
nenhum teste unitário, de integração ou de componente depende de uma
instância real rodando.

## Cobertura de testes

Backend (pytest + coverage): **97%** de cobertura de linhas (mínimo exigido: 80%).
Frontend (vitest + v8 coverage): **~91% statements / 79% branches / 90%
functions / 94% lines** (mínimo exigido: 70% em todas as métricas).
O workflow em `.github/workflows/ci.yml` recalcula esses números a cada push.

## Módulos

| Módulo | O que demonstra | Spec |
|---|---|---|
| RAG | Chunking, embeddings, busca vetorial, prompt grounding, citação de fontes | [`specs/rag.spec.md`](specs/rag.spec.md) |
| Chatbot | Sessões, histórico com janela deslizante, streaming SSE | [`specs/chatbot.spec.md`](specs/chatbot.spec.md) |
| Agente | LangGraph state machine, tool calling, limites de segurança (leitura apenas, cap de iterações) | [`specs/agent.spec.md`](specs/agent.spec.md) |
| Fine-tuning (V2) | Documentado, não implementado nesta rodada | [`specs/finetune.spec.md`](specs/finetune.spec.md) |

## Roadmap

- **Fine-tuning (V2)**: treino LoRA via Unsloth (r=16, alpha=32) sobre um
  modelo base, exportação para `.gguf` quantizado (Q4_K_M) e registro no
  Ollama via `Modelfile`. Adiado porque exige GPU NVIDIA/CUDA, indisponível
  no ambiente de desenvolvimento atual (Mac). O comportamento esperado está
  documentado em `specs/finetune.spec.md` para quando essa GPU estiver
  disponível.
- **E2E real**: os specs Playwright em `e2e/` estão escritos mas não foram
  executados nesta sessão — requerem `ollama pull llama3.2` e
  `ollama pull nomic-embed-text` (só `qwen3` está instalado aqui), além do
  frontend e backend rodando localmente.
- **Demo GIF**: gravar após os modelos serem baixados (ver seção Demo acima).

## Variáveis de ambiente

Nenhum segredo é commitado: `backend/.env` e `frontend/.env` estão no
`.gitignore`; use `backend/.env.example` e `frontend/.env.example` como
referência.
