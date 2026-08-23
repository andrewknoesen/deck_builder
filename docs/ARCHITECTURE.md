# MTG Deck Builder - Architecture

> **Status: refreshed 2026-08-23**, current through Phase 9 (`PLAN.md`). Originally written
> 2026-07-08; this replaces the earlier `ARCHITECTURE.md`/`AI_ARCHITECTURE.md`, which were
> pre-implementation planning docs describing features (a `DeckAdvisorAgent` chat widget with
> `search_cards`/`get_deck_stats` tools) that were never built as specified. See `docs/README.md`
> for the full docs index — this page is linked from there, not a replacement for it.

## 1. Overview

- **Frontend**: React 18 + TypeScript + Vite, styled with Tailwind and MUI. Talks to the backend
  REST API and renders deck-building UI, stats, and an agent chat page.
- **Backend**: FastAPI service, the single source of truth for user/deck data. Proxies card data
  from Scryfall rather than storing full card details.
- **Database**: SQLModel (SQLAlchemy + Pydantic) ORM. Default `DATABASE_URL` is Postgres via
  `asyncpg`; async SQLite is used in tests. Migrations via Alembic (`backend/alembic/`).
- **Card data**: Scryfall API is the sole authority — see `backend/app/services/scryfall.py`
  (`ScryfallService`, async `httpx` client). Never hallucinate card data.
- **AI / Agent layer**: Google ADK. See `backend/app/ai/README.md` for the full breakdown. Two
  agents exist — `rules_agent`, an L3-judge agent with rules/glossary/ruling-lookup tools backed
  by a Chroma-indexed RAG over the MTG comprehensive rules; and `deck_advisor_agent`, which
  suggests additions/cuts for a specific deck using a stateless `search_cards` Scryfall tool plus
  deck stats/list folded into its prompt context (no DB-aware tools — see
  `backend/app/ai/agents/deck_advisor/deck_advisor_agent.py`). Both are built via the shared
  `make_agent` factory in `backend/app/ai/agents/factory.py`. A third tool,
  `search_cards_semantic` (`backend/app/ai/tools/cards.py`), queries a separate `CardRAG`/
  `mtg_cards` Chroma collection (`backend/app/ai/rag/cards.py`) for synergy-style semantic search
  over card oracle text — used by `deck_advisor_agent` and by the frontend's per-card synergy
  lookup (Phase 6, frontend-only, no new backend endpoint).
- **MCP server**: `backend/app/mcp/server.py` exposes all five AI tools (`search_cards`,
  `search_cards_semantic`, `query_comprehensive_rules`, `lookup_glossary_term`,
  `lookup_card_rulings`) to external MCP clients over stdio — a separate process, bypasses ADK and
  FastAPI entirely. See `docs/mcp_server.md` for the full design and setup.
- **Auth**: Google OAuth is the intended flow (ID token from the frontend, verified on the
  backend), but `backend/app/api/deps.py:get_current_user` is currently a **dev-mode stub** — it
  does not verify Google ID tokens yet; it returns/creates a placeholder dev user. Real ID token
  verification is a TODO, not implemented.

## 2. Directory Structure

See the root `CLAUDE.md` for the maintained directory tree — it's kept current there rather than
duplicated here.

## 3. API

Base URL: `/api/v1` (mounted in `backend/app/api/api.py`).

| Router | Prefix | Notes |
|---|---|---|
| `auth` | `/auth` | `POST /login` |
| `users` | `/users` | `POST /`, `GET /me` |
| `cards` | `/cards` | `GET /search`, `GET /{card_id}` — Scryfall proxy |
| `decks` | `/decks` | Full CRUD + `GET /{deck_id}/stats` + `POST /import` (paste-text import, best-effort — see `backend/app/services/deck_import.py`) |
| `collection` | `/collection` | Full CRUD for a user's card collection |
| `ai` | `/ai` | `POST /chat` (wired to `rules_agent`), `POST /suggest` (wired to `deck_advisor_agent`; takes `deck_id` + `query`, ownership-checked like every other deck route) |
| `goldfish` | `/goldfish` | `POST /sessions` (auto-creates a shuffled "Game start" root node; takes an optional `opponent_deck_id` for two-deck sessions, Phase 3d), `GET /sessions?deck_id=`, `GET /sessions/{id}` (flat node list, client builds the tree), `PATCH /sessions/{id}` (records a session outcome, Phase 7), `GET /analytics` (aggregate outcome stats across sessions, Phase 7), `POST /sessions/{id}/nodes` (free-text label/trackers, or a structured `action` — draw/play_land/cast/move_zone/set_life/shuffle/next_turn, each with a `self`/`opponent` `target` — applied server-side against the parent's `state`, including running `mana_spent`/`opponent_mana_spent` totals on `cast`, Phase 8), `DELETE /nodes/{id}` (cascades to descendants) — practice-mode branching action tree + assisted simulator, Phase 3a+3b+3d+7+8 |

For exact request/response shapes, read the router file directly (`backend/app/api/routes/`) and
its paired schema in `backend/app/schemas/` — they're the source of truth, not this doc.

## 4. What's not built yet

Kept here deliberately so this doc doesn't silently go stale again the way its predecessor did:

- **Real Google ID token verification**: see the Auth note above.
- **Practice Mode / goldfishing, 3c**: 3a (manual action log + branching tree), 3b (real
  library/hand/battlefield/graveyard/exile state, structured actions, mini-playmat UI), and 3d
  (a second, fully-manual opponent board) are all built — see the `goldfish` router above. 3c
  (rules-aware legality/resolution) is not — explicitly parked, no next-pick-up trigger, see
  `PLAN.md`'s Phase 3 for the staged design.
- **Scryfall bulk-data ingestion — refresh script built, scheduling still open**:
  `backend/app/ai/ingestion/scryfall_ingestion.py`'s `run_ingestion()` pulls Scryfall's
  `default_cards` bulk file and upserts it into the local `Card` table (batched insert/update, not
  the one-row-at-a-time pattern `sync_cards` uses). `search_cards` (`backend/app/ai/tools/cards.py`)
  now checks that local cache first for plain name queries via a dedicated tool-side DB session
  (`backend/app/ai/tools/db.py` — ADK tools have no FastAPI-style DI, so this can't reuse
  `Depends(get_db)`), falling back to a live Scryfall call when the cache misses or the query uses
  Scryfall's `key:value` operator syntax (`t:`, `c:`, `f:`, ...), which the local cache doesn't
  replicate. **Still open**: the script is run by hand (`uv run python -m
  app.ai.ingestion.scryfall_ingestion`), not on any schedule — deferred until there's a real
  deployment target to schedule against (see Deferred in `PLAN.md`). Until it's run at least once,
  or if a card isn't in the bulk snapshot yet, `search_cards` transparently falls back to live
  Scryfall exactly as before.
- **MCP server over HTTP/SSE**: `backend/app/mcp/server.py` (Phase 9) only serves stdio today —
  a local-process-only transport. HTTP/SSE is explicitly gated on real auth landing first (see the
  Auth note above and `docs/mcp_server.md`), not a "later at our leisure" item.
