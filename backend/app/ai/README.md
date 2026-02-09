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
-   **`rules.py`**: Implementation for MTG Rules (`RulesRAG`).
-   **Usage**: `from app.ai.rag.rules import get_rules_rag; rag = get_rules_rag()`

### 5. `agents/`
**AI Agents.**
-   **`rules.py`**: `RulesAgent`.
-   **Usage**: `from app.ai.agents.rules import get_rules_agent; agent = get_rules_agent()`

### 6. `tools/`
**Agent Tools.**
-   **`rules.py`**: `query_comprehensive_rules`.
-   **`scryfall.py`**: `lookup_card_rulings`.

## Development Guidelines
1.  **Imports**: Always import shared types from `app.ai.types`.
2.  **Vector Store**: Use the interfaces in `app.ai.vector_store.base` for type hinting, but instantiate concrete classes from their respective files (or a factory).
3.  **New Features**:
    -   If adding a new data capability, add models to `types.py`.
    -   If adding a new backend (e.g., Pinecone), add a new file in `vector_store/` implementing `VectorStore`.
