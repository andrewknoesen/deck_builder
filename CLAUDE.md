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

## Documentation

`docs/README.md` is the central docs index — the one place both agents and human developers
should be able to find everything (architecture, subsystem design docs, the decision-making
process, the subagent roster, how to explore the codebase structurally) without already knowing a
file exists. This file (`CLAUDE.md`) is always loaded automatically and doesn't need routing to;
`docs/README.md`'s job is bridging from here to everything else. It's also published as a hosted
mkdocs site (`mkdocs.yml`, `.github/workflows/docs.yml` — builds on every `docs/**` push to
`main`) for human browsing; agents should keep reading the raw files directly via `Read`/`Grep`
rather than fetching the hosted URL. Links inside `docs/README.md` that point outside `docs/`
(e.g. to this file, or to `backend/app/ai/README.md`) are full GitHub URLs rather than relative
paths, since mkdocs only serves the `docs/` folder — keep that convention for any new outbound
link added there.

**Convention**: any new persistent doc file anywhere in the repo (`docs/*.md`, a new subdirectory
`README.md`, a new `.claude/agents/*.md`) gets linked from `docs/README.md` as part of that
phase's Concrete Steps — the same "update the doc" discipline `PLAN.md` already applies to
`docs/ARCHITECTURE.md`'s "what's not built yet" section, widened to cover the index itself. This
is process, not tooling — there's no CI to enforce it, so it depends on whoever's implementing a
phase actually doing it.

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

- `/ponytail` (`.claude/commands/`) — Lazy senior dev mode. Enforces YAGNI, stdlib-first, shortest working diff. Use by default unless the task explicitly needs complexity.

## Subagent roster

`.claude/agents/` defines a project-specific "team" of subagents — Claude dispatches to the right one(s) automatically based on the task, matched against each agent's `description`. No manual invocation needed; this replaced an earlier set of manually-run `/mtg-*` slash commands and a `/bootstrap` coordinator for exactly that reason. Each agent reads `CLAUDE.md`/`PLAN.md` itself before acting, so this list stays short — see the agent file for the actual grounding and standards.

- `mtg-architect` — cross-cutting design/blueprint (module placement, API/data-model shape, phasing). Read-only; hands off implementation.
- `mtg-backend` — FastAPI routes, SQLModel models, schemas, services, Alembic migrations.
- `mtg-frontend` — React/TS pages, components, hooks, API client wiring.
- `mtg-devops` — Docker Compose, Dockerfiles, health checks, local dev environment.
- `mtg-integrations` — Scryfall API + the (deliberately stubbed) Google auth integration.
- `mtg-ai-engineer` — the ADK agent layer (`backend/app/ai/`): agents, tools, RAG, ingestion.
- `mtg-maths` — deck-statistics domain math (mana curve, draw odds, land counts, color balance).
- `mtg-em` — task breakdown, role routing, and status/priority audits against `PLAN.md`. Read-only; doesn't write code.
- `mtg-ux` — visual/interaction design and critique for the frontend, distinct from `mtg-frontend`'s implementation focus.
- `mtg-qa` — dedicated test coverage, edge-case hunting, and full-suite verification.
