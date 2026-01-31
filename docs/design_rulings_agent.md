# AI Rulings Agent Design

**Status**: Draft
**Target Audience**: @[/mtg-ai-engineer], @[/mtg-backend], @[/mtg-frontend]

This document outlines the architecture and implementation plan for the **Rulings Agent**, optimized for **low latency and cost efficiency**.

## 1. Overview

The Rulings Agent serves as a "Rules Lawyer" to answer MTG questions.
**Constraint**: Must maintain low token usage and fast response times.

## 2. Architecture & Data Strategy (Cost-Optimized)

To minimize costs and latency, we will use a **Retrieval Augmented Generation (RAG)** approach rather than loading the entire Comprehensive Rules (CR) into context.

**Rationale**:
- Full CR is ~2MB text (~500k+ tokens). Repeatedly sending this is slow and expensive.
- Detailed RAG allows us to send only the ~5-10 relevant rules (~2k tokens), significantly improving speed.

### 2.1. Knowledge Base
1.  **Comprehensive Rules (CR)**:
    - **Chunking Strategy**: Split by Rule ID (e.g., `702.1`, `100.1a`). Each rule is a distinct chunk.
    - **Embeddings**: Generate embeddings for all ~2000+ rule chunks using **nomic-ai/nomic-embed-text-v1** (HuggingFace).
    - **Rationale**: Local execution (zero cost), High performance, Long context (8192) suitable for complex rules.
    - **Storage**: In-memory vector index (e.g., FAISS or simple cosine similarity with numpy) loaded at startup. The dataset is small enough (<10MB total with embeddings) to fit in RAM.

2.  **Card Oracle & Rulings**:
    - Retrieved on-demand via Scryfall Tool.

### 2.2. The Pipeline
1.  **User Query**: "Does Deathtouch work on Planeswalkers?"
2.  **Keyword/Semantic Search**:
    - Identify key terms ("Deathtouch", "Planeswalker").
    - Search Vector Index for top 10 relevant CR chunks.
3.  **Card Lookup** (if card names detected):
    - Fetch official rulings from Scryfall.
4.  **Context Assembly**:
    - Combine: `User Query` + `Retrieved CR Rules` + `Card Rulings`.
5.  **LLM Call**:
    - Send to `gemini-2.0-flash` (fast, cheap) to synthesize the answer.

## 3. Workflow & Task Order

This project must be executed in the following order using the specified workflows.

### Phase 1: Core Agent & RAG Setup
**Workflow**: `@[/mtg-ai-engineer]`

1.  **Data Ingestion**:
    - Create `backend/scripts/ingest_rules.py`:
        - Download CR text.
        - Parse/Chunk into JSON structure `{"id": "702.2", "text": "..."}`.
        - Generate and save embeddings in `chromadb`.
2.  **Vector Store**:
    - Implement `backend/app/ai/rag.py`:
        - Load index on startup.
        - `query_rules(query: str, k=10) -> List[str]`.
3.  **Agent Logic**:
    - Create `RulesAgent` in `backend/app/ai/agents.py`.
    - Tools: `rag.query_rules`, `scryfall.get_rulings`.

### Phase 2: API & Integration
**Workflow**: `@[/mtg-backend]`

1.  **Endpoint**:
    - `POST /api/v1/ai/rulings`
    - Input: `{ query: "..." }`
    - Logic: Instantiate `RulesAgent` -> Invoke -> Return stream/text.
2.  **Docker**:
    - Ensure `backend/Dockerfile` includes necessary libraries (numpy, scikit-learn, or vector store lib).

### Phase 3: Frontend UI
**Workflow**: `@[/mtg-frontend]`

1.  **Chat Widget**:
    - Add "Ask a Judge" feature in the Deck Builder.
    - Call `/api/v1/ai/rulings`.
    - Display Citations (Rule numbers) clearly.

## 4. Implementation Details for @[/mtg-ai-engineer]

### Directories
```text
backend/app/ai/
├── data/
│   ├── rules.json       # Source text
│   └── rules.index      # Vector index
├── rag.py               # Retrieval logic
├── agents.py            # Agent definition
└── tools.py             # Tools
```

### Prompt Engineering (System Instruction)
> "You are an MTG Rules Judge. Answer using ONLY the provided context rules and rulings.
> If the context is insufficient, state that you are unsure.
> Always cite the Rule Number (e.g., [CR 702.1]) when explaining."

### Cost Control
- **Model**: `gemini-2.0-flash` (or `gemini-1.5-flash`).
- **Input Limit**: Cap retrieved chunks to ~10-15 to keep input <4k tokens.
