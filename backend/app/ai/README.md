# AI Module Documentation

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
**Data Processing Pipelines.**
-   **`base.py`**: Ingestion-specific ABCs (`IngestionSource`, `ContentSplitter`, `SectionParser`).
-   **`rules_ingestion.py`**: Concrete script for downloading, parsing, and indexing MTG rules.
-   **Usage**: Run `rules_ingestion.py` to populate the vector database.

### 4. `rag/`
**RAG Modules.**
-   **`base.py`**: ABC `RAGService`.
-   **`rules.py`**: Implementation for MTG Rules (`RulesRAG`), exposed as a module-level singleton.
-   **Usage**: `from app.ai.rag.rules import rules_rag; docs = rules_rag.query("declare blockers", k=5)`

### 5. `agents/`
**AI Agents.** Each agent is a plain [Google ADK](https://google.github.io/adk-docs/) `Agent`
instance — a prompt string plus a list of tool functions — not a custom class. ADK's `Agent`
already handles the model loop and tool dispatch, so there's no in-repo base class to extend.
-   **`rules/rules_agent.py`**: `rules_agent` — an L3-judge agent wired to `gemini-2.5-flash`
    with the rules/glossary/ruling tools below.
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
class is needed.
-   **`rules.py`**: `query_comprehensive_rules`, `lookup_glossary_term`.
-   **`scryfall.py`**: `lookup_card_rulings` (async, hits Scryfall via `ScryfallService`).

## Development Guidelines
1.  **Imports**: Always import shared types from `app.ai.types`.
2.  **Vector Store**: Use the interfaces in `app.ai.vector_store.base` for type hinting, but instantiate concrete classes from their respective files (or a factory).
3.  **New Features**:
    -   If adding a new data capability, add models to `types.py`.
    -   If adding a new backend (e.g., Pinecone), add a new file in `vector_store/` implementing `VectorStore`.
    -   If adding a new tool, write it as a plain function (see `tools/rules.py`) and register it
        directly on the relevant `Agent`'s `tools=[...]` list — don't wrap it in a class.
