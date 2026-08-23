# MCP server

`backend/app/mcp/server.py` exposes this app's existing AI tool functions to
external MCP clients (Claude Desktop, another local agent) over the [Model
Context Protocol](https://modelcontextprotocol.io/), using the official
`mcp` Python SDK's `FastMCP` — no wrapping, no ADK involvement. It runs as a
separate local process (stdio transport only, no network listener) and never
imports or boots the FastAPI app.

## What's exposed

All five of this app's existing read-only ADK tool functions, imported
directly from `app.ai.tools.*` with their original names and docstrings:

- `search_cards` — Scryfall-syntax card search (local cache, falls back to live Scryfall)
- `search_cards_semantic` — synergy/mechanic search over the card RAG index
- `query_comprehensive_rules` — MTG Comprehensive Rules RAG lookup
- `lookup_glossary_term` — MTG glossary RAG lookup
- `lookup_card_rulings` — official Scryfall rulings for named cards

Nothing here mutates a deck, collection, or goldfish session — deck-mutating
capabilities aren't exposed via MCP today. See `PLAN.md`'s Phase 9 for the
full design rationale.

## Running it

From `backend/`, with `.env` configured the same way it is for local
development (`DATABASE_URL`, `CHROMA_HOST`/`CHROMA_PORT`, `SCRYFALL_BASE_URL`
— see `backend/.env.example`) and the docker-compose Postgres/ChromaDB
services up (`docker compose up -d db chromadb` from the repo root):

```bash
cd backend
uv run python -m app.mcp.server
```

This blocks, talking MCP over stdin/stdout — it's meant to be spawned by an
MCP client, not run interactively on its own.

## Pointing an MCP client at it

Example `claude_desktop_config.json` entry:

```json
{
  "mcpServers": {
    "deck_builder": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/absolute/path/to/deck_builder/backend",
        "python",
        "-m",
        "app.mcp.server"
      ]
    }
  }
}
```

Any MCP client that can spawn a local stdio subprocess works the same way —
just point `command`/`args` at the same `uv run --project <path-to-backend>
python -m app.mcp.server` invocation.

## Trust boundary

stdio only, no HTTP/SSE — whoever can run the above command already has the
same local access as running any other script in this repo (`.env`, DB,
Scryfall credentials). This app's auth is currently a dev-mode stub (see
`CLAUDE.md`/`PLAN.md`), which is fine for a locally-spawned subprocess but is
an explicit, hard blocker on ever exposing this over a network transport —
not planned for this server.
