# AI Module Documentation

> **Status: refreshed 2026-08-23**, current through Phase 9 (`PLAN.md`). See `docs/README.md` for
> the full docs index.

This directory (`backend/app/ai`) contains the core logic for the application's AI features, including RAG (Retrieval-Augmented Generation) and Agentic capabilities.

## Directory Structure

### 1. `types.py`
**Pure Data Models.**
-   Contains shared Pydantic models used across the AI subsystem.
-   **Rule**: Must have ZERO dependencies on other internal AI modules to prevent circular imports.
-   **Key Models**: `PipelineContext`, `ProcessedChunk`.

### 2. `vector_store/`
**Vector Database & Embedding Logic.**
-   **`base.py`**: Abstract Base Classes (ABCs) for `VectorStore` and `EmbeddingModel`.
-   **`chroma.py`**: Concrete implementation using ChromaDB.
-   **`embedding.py`**: Concrete implementation using SentenceTransformers (local embeddings).
-   **Usage**: Import `VectorStore` or `EmbeddingModel` from here when building services.

### 3. `ingestion/`
**Data Processing Pipelines.** All run by hand (`uv run python -m app.ai.ingestion.<module>`),
deliberately not scheduled — see Deferred in `PLAN.md`.
-   **`base.py`**: Ingestion-specific ABCs (`IngestionSource`, `ContentSplitter`, `SectionParser`).
-   **`rules_ingestion.py`**: Downloads, parses, and indexes MTG rules into `rag/rules.py`'s Chroma
    collection.
-   **`card_embedding_ingestion.py`**: Embeds card oracle text into `rag/cards.py`'s `mtg_cards`
    Chroma collection, powering `search_cards_semantic`.
-   **`scryfall_ingestion.py`**: `run_ingestion()` refreshes the local `Card` table from Scryfall's
    bulk `default_cards` file (batched, not the `sync_cards` one-row-at-a-time path) — the cache
    `search_cards` checks before falling back to live Scryfall.

### 4. `rag/`
**RAG Modules.**
-   **`base.py`**: ABC `RAGService`.
-   **`rules.py`**: Implementation for MTG Rules (`RulesRAG`), exposed as a module-level singleton
    `rules_rag`.
-   **`cards.py`**: Implementation for card oracle-text synergy search (`CardRAG`), exposed as a
    module-level singleton `card_rag`, backed by a separate `mtg_cards` Chroma collection. Shares
    the same sentence-transformer embedder as `RulesRAG`.
-   **Usage**: `from app.ai.rag.rules import rules_rag; docs = rules_rag.query("declare blockers", k=5)`

### 5. `agents/`
**AI Agents.** Each agent is a plain [Google ADK](https://google.github.io/adk-docs/) `Agent`
instance — a prompt string plus a list of tool functions — not a custom class. ADK's `Agent`
already handles the model loop and tool dispatch, so there's no in-repo base class to extend.
-   **`rules/rules_agent.py`**: `rules_agent` — an L3-judge agent wired to `gemini-2.5-flash`
    with the rules/glossary/ruling tools below.
-   **`deck_advisor/deck_advisor_agent.py`**: `deck_advisor_agent` — suggests additions/cuts for a
    specific deck, using `search_cards`/`search_cards_semantic` plus deck stats/list folded into
    its prompt context (no DB-aware tools, by design — see Phase 1 in `PLAN.md`).
-   **`factory.py`**: `make_agent(name, description, prompt, tools)` — the shared factory both
    agents above are built from (extracted once a second agent showed real
    `model=settings.AI_MODEL_NAME`-style duplication, per the "resist a class hierarchy" rule
    below actually firing).
-   **Usage**: agents aren't called directly — invoke them through an ADK `Runner`:
    ```python
    from google.adk.runners import InMemoryRunner
    from google.genai import types as genai_types
    from app.ai.agents.rules.rules_agent import rules_agent

    runner = InMemoryRunner(agent=rules_agent)
    session = await runner.session_service.create_session(app_name=runner.app_name, user_id="u1")
    message = genai_types.Content(role="user", parts=[genai_types.Part(text="How does trample work?")])
    async for event in runner.run_async(user_id=session.user_id, session_id=session.id, new_message=message):
        ...  # see backend/app/api/routes/ai.py for the full pattern
    ```
-   **Adding a new agent**: create a new subfolder under `agents/` with its own prompt + tools +
    module-level `Agent(...)` instance, following `rules/rules_agent.py`. If a second agent
    introduces real duplication (e.g. repeated `model=settings.AI_MODEL_NAME` boilerplate), pull
    it into a thin factory *function* — resist reaching for a class hierarchy.

### 6. `tools/`
**Agent Tools.** Plain (sync or async) functions passed directly into an `Agent`'s `tools=[...]`
list — ADK generates the function-calling schema from the signature and docstring, so no wrapper
class is needed. All five are self-contained (own DB session or HTTP client per call, no FastAPI
request-cycle dependency) — this is what makes them directly reusable outside ADK entirely, see
`backend/app/mcp/` below.
-   **`rules.py`**: `query_comprehensive_rules`, `lookup_glossary_term`.
-   **`scryfall.py`**: `lookup_card_rulings` (async, hits Scryfall via `ScryfallService`).
-   **`cards.py`**: `search_cards` (checks the local `Card` cache for plain-name queries via
    `db.py`'s session, falls back to live Scryfall), `search_cards_semantic` (queries `rag/cards.py`'s
    `CardRAG` for synergy-style search over oracle text).
-   **`db.py`**: `get_tool_session()` — a directly-importable `async_sessionmaker` bound to the
    shared engine, built specifically because ADK calls tool functions directly (no FastAPI
    request/route cycle, so no `Depends(get_db)`).

## `backend/app/mcp/` — exposing these tools outside ADK

A sibling package, not a subfolder of `app/ai/` — it's a server entry point, not a tool
implementation. `server.py` registers all five tool functions above directly on a `FastMCP`
instance and serves them over stdio to external MCP clients (Claude Desktop, another local agent).
Never imports ADK or FastAPI — a direct payoff of the tools above being plain, self-contained
functions. See `docs/mcp_server.md` for the full design, setup, and the auth/transport reasoning
for why this is stdio-only for now.

## Development Guidelines
1.  **Imports**: Always import shared types from `app.ai.types`.
2.  **Vector Store**: Use the interfaces in `app.ai.vector_store.base` for type hinting, but instantiate concrete classes from their respective files (or a factory).
3.  **New Features**:
    -   If adding a new data capability, add models to `types.py`.
    -   If adding a new backend (e.g., Pinecone), add a new file in `vector_store/` implementing `VectorStore`.
    -   If adding a new tool, write it as a plain function (see `tools/rules.py`) and register it
        directly on the relevant `Agent`'s `tools=[...]` list — don't wrap it in a class.
