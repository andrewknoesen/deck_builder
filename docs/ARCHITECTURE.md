# MTG Deck Builder - Architecture

Reflects the actual current implementation as of `feature/agent_factory` (2026-07-08). This
replaces the earlier `ARCHITECTURE.md`/`AI_ARCHITECTURE.md`, which were pre-implementation
planning docs describing features (a `DeckAdvisorAgent` chat widget with `search_cards`/
`get_deck_stats` tools) that were never built as specified.

## 1. Overview

- **Frontend**: React 18 + TypeScript + Vite, styled with Tailwind and MUI. Talks to the backend
  REST API and renders deck-building UI, stats, and an agent chat page.
- **Backend**: FastAPI service, the single source of truth for user/deck data. Proxies card data
  from Scryfall rather than storing full card details.
- **Database**: SQLModel (SQLAlchemy + Pydantic) ORM. Default `DATABASE_URL` is Postgres via
  `asyncpg`; async SQLite is used in tests. Migrations via Alembic (`backend/alembic/`).
- **Card data**: Scryfall API is the sole authority — see `backend/app/services/scryfall.py`
  (`ScryfallService`, async `httpx` client). Never hallucinate card data.
- **AI / Agent layer**: Google ADK. See `backend/app/ai/README.md` for the full breakdown. One
  agent currently exists — `rules_agent`, an L3-judge agent with rules/glossary/ruling-lookup
  tools backed by a Chroma-indexed RAG over the MTG comprehensive rules.
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
| `ai` | `/ai` | `POST /chat` (wired to `rules_agent`), `POST /suggest` (**placeholder** — returns a canned response, not implemented) |

For exact request/response shapes, read the router file directly (`backend/app/api/routes/`) and
its paired schema in `backend/app/schemas/` — they're the source of truth, not this doc.

## 4. What's not built yet

Kept here deliberately so this doc doesn't silently go stale again the way its predecessor did:

- **Deck advisor / chat-based deck suggestions**: `POST /ai/suggest` is a placeholder. There is
  no agent with `search_cards` or `get_deck_stats` tools — only the rules-judge agent exists.
- **Real Google ID token verification**: see the Auth note above.
- **Multi-agent abstraction**: agents are plain ADK `Agent` instances (see
  `backend/app/ai/README.md`); there is currently no shared base class or factory, by design —
  revisit only once a second agent exists and real duplication shows up.
