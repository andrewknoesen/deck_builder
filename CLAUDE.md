# deck_builder

AI-powered Magic: The Gathering deck building assistant. FastAPI backend + React/TypeScript frontend with a Google ADK agent layer for rules lookups, card analysis, and deck suggestions. Target: a public SaaS for serious MTG players.

**Active branch:** `feature/agent_factory`
**Repo:** https://github.com/andrewknoesen/deck_builder

---

## Architecture

```
deck_builder/
├── backend/                    ← FastAPI app (uv, Python 3.13)
│   └── app/
│       ├── ai/                 ← Agent layer (ADK, RAG, tools)
│       │   ├── agents/
│       │   │   └── rules/      ← rules_agent (ADK Agent, Gemini model)
│       │   ├── tools/
│       │   │   ├── rules.py    ← query_comprehensive_rules, lookup_glossary_term
│       │   │   └── scryfall.py ← lookup_card_rulings
│       │   ├── rag/            ← Chroma vector store querying
│       │   ├── ingestion/      ← MTG rules text ingestion pipeline
│       │   └── vector_store/   ← Chroma client setup
│       ├── api/routes/         ← FastAPI routers (ai, auth, cards, decks, collection, users)
│       ├── core/               ← config (pydantic-settings), db, logging
│       ├── models/             ← SQLModel ORM models
│       ├── schemas/            ← Pydantic request/response schemas
│       └── services/           ← ScryfallService (httpx async client)
├── frontend/                   ← React 18, TypeScript, Vite, Tailwind, MUI
│   └── src/
│       ├── pages/              ← AgentChat, DeckBuilder, DeckList, Collection, LandingPage
│       ├── api/                ← API client layer
│       ├── components/         ← Shared UI components
│       ├── context/            ← React context providers (e.g. auth)
│       ├── hooks/              ← Custom React hooks
│       ├── types/              ← Shared TypeScript types
│       ├── utils/              ← Helpers
│       ├── styles/             ← Global styles
│       └── assets/             ← Static assets
└── docker-compose.yml          ← Local dev stack
```

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, SQLModel, Alembic, uv |
| Frontend | React 18, TypeScript, Vite, Tailwind, MUI |
| Database | SQLite (dev), PostgreSQL (prod path, asyncpg) |
| AI | Google ADK, Gemini 2.5 Flash, Chroma, sentence-transformers |
| Card Data | Scryfall API |
| Infra | Docker Compose |

---

## Agent Layer

The AI layer lives in `backend/app/ai/`. Current state:

- **`rules_agent`** — Google ADK `Agent` wired to `gemini-2.5-flash`. Tools: `query_comprehensive_rules`, `lookup_glossary_term`, `lookup_card_rulings`. Acts as an L3 judge. Lives at `backend/app/ai/agents/rules/rules_agent.py`.
- **RAG** — MTG Comprehensive Rules ingested into Chroma. Query via `backend/app/ai/rag/`.
- **Scryfall tools** — Async HTTP via `ScryfallService` (`backend/app/services/scryfall.py`).

Config lives in `backend/app/core/config.py` (pydantic-settings). Key env vars: `GOOGLE_API_KEY`, `CHROMA_HOST`, `AI_MODEL_NAME` (default: `gemini-2.5-flash`).

---

## Dev Setup

`backend/` is a standalone uv project — its own `pyproject.toml`, `uv.lock`, and `.venv`, all
inside `backend/`. There is no repo-wide uv workspace; the root `pyproject.toml` exists only to
give editors opened at the repo root the right `pyright`/`mypy` paths.

```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Full stack
docker compose up
```

---

## Key Conventions

- **Card data = Scryfall only.** Never hallucinate card names, costs, or rules text. Use `ScryfallService` or the Scryfall tools.
- **Agent tools are plain async functions** registered directly on the ADK `Agent` — not classes. See `tools/rules.py` for the pattern.
- **New agents** are plain ADK `Agent` instances (see `agents/rules/rules_agent.py`) and live in their own subfolder under `agents/`. If a second agent introduces real duplication (e.g. repeated `model=settings.AI_MODEL_NAME` boilerplate), extract a thin factory *function* — not a class hierarchy.
- **Backend REST endpoints** live under `/api/...` and are the single source of truth for data.
- **Auth** defaults to Google login (Google SDK on the frontend, ID token verified on the backend).
- **Migrations** via Alembic in `backend/alembic/`. Run `uv run alembic upgrade head`.
- **Ruff** for linting/formatting: `uv run ruff check . && uv run ruff format .`
- **Tests**: update or add pytest (backend) / React Testing Library (frontend) tests alongside feature changes. Manually re-run tests and, for frontend changes, verify in the browser before calling work done.
- **Config** is env-driven (`.env` files) — no hard-coded secrets or URLs.

---

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

---

## Skills

Custom slash commands live in `.claude/commands/`:

- `/ponytail` — Lazy senior dev mode. Enforces YAGNI, stdlib-first, shortest working diff. Use by default unless the task explicitly needs complexity.
- `/bootstrap` — Coordinator that walks through the other MTG persona workflows in order.
- `/mtg-architect` — Lead architect persona for high-level design/task breakdown.
- `/mtg-backend` — Backend FastAPI engineer persona.
- `/mtg-frontend` — Frontend React engineer persona.
- `/mtg-devops` — Docker/infra engineer persona.
- `/mtg-integrations` — Google auth & Scryfall integrations persona.
- `/mtg-ai-engineer` — ADK agent engineer persona.
- `/mtg-maths` — MTG deck-stats/math persona (mana curve, draw odds, land counts).
