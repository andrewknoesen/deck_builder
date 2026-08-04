# Graph Report - .  (2026-08-04)

## Corpus Check
- 179 files · ~54,463 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 910 nodes · 1662 edges · 103 communities (81 shown, 22 thin omitted)
- Extraction: 79% EXTRACTED · 21% INFERRED · 0% AMBIGUOUS · INFERRED: 344 edges (avg confidence: 0.53)
- Token cost: 254,253 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Scryfall Card Sync|Scryfall Card Sync]]
- [[_COMMUNITY_Backend App Entrypoint|Backend App Entrypoint]]
- [[_COMMUNITY_Frontend NPM Dependencies|Frontend NPM Dependencies]]
- [[_COMMUNITY_Rules Ingestion Parsers|Rules Ingestion Parsers]]
- [[_COMMUNITY_AI Engineer Persona & Docker Stack|AI Engineer Persona & Docker Stack]]
- [[_COMMUNITY_Goldfish Session Schemas|Goldfish Session Schemas]]
- [[_COMMUNITY_Ingestion Pipeline Base Classes|Ingestion Pipeline Base Classes]]
- [[_COMMUNITY_Goldfish Actions Tests|Goldfish Actions Tests]]
- [[_COMMUNITY_RAG Base Interfaces|RAG Base Interfaces]]
- [[_COMMUNITY_Frontend App TS Config|Frontend App TS Config]]
- [[_COMMUNITY_Scryfall Bulk Ingestion Script|Scryfall Bulk Ingestion Script]]
- [[_COMMUNITY_Goldfish Playmat & Tree UI|Goldfish Playmat & Tree UI]]
- [[_COMMUNITY_Frontend Node TS Config|Frontend Node TS Config]]
- [[_COMMUNITY_Deck Import Tests|Deck Import Tests]]
- [[_COMMUNITY_Chroma Vector Store & Settings|Chroma Vector Store & Settings]]
- [[_COMMUNITY_Deck Stats UI Components|Deck Stats UI Components]]
- [[_COMMUNITY_Deck Import Parsing Service|Deck Import Parsing Service]]
- [[_COMMUNITY_AI & Goldfish Schemas|AI & Goldfish Schemas]]
- [[_COMMUNITY_Deck Card UI Components|Deck Card UI Components]]
- [[_COMMUNITY_API Client & Deck List UI|API Client & Deck List UI]]
- [[_COMMUNITY_Card & Collection Models|Card & Collection Models]]
- [[_COMMUNITY_Deck Advisor Chat UI|Deck Advisor Chat UI]]
- [[_COMMUNITY_search_cards Tool Tests|search_cards Tool Tests]]
- [[_COMMUNITY_PLAN.md Decisions & Ingestion|PLAN.md Decisions & Ingestion]]
- [[_COMMUNITY_Deck Builder Search & Hover Hooks|Deck Builder Search & Hover Hooks]]
- [[_COMMUNITY_Card Hover Context|Card Hover Context]]
- [[_COMMUNITY_Frontend Auth Context|Frontend Auth Context]]
- [[_COMMUNITY_Ingestion Pipeline Types|Ingestion Pipeline Types]]
- [[_COMMUNITY_ScryfallService Client|ScryfallService Client]]
- [[_COMMUNITY_Deck Import Feature & Auth Docs|Deck Import Feature & Auth Docs]]
- [[_COMMUNITY_Frontend Pages & Card Hover Preview|Frontend Pages & Card Hover Preview]]
- [[_COMMUNITY_GoldfishNodeSession Models|GoldfishNode/Session Models]]
- [[_COMMUNITY_Deck Stats Calculation Service|Deck Stats Calculation Service]]
- [[_COMMUNITY_AI SuggestChat Route Tests|AI Suggest/Chat Route Tests]]
- [[_COMMUNITY_AI Module Architecture Docs|AI Module Architecture Docs]]
- [[_COMMUNITY_Top-Level Architecture Overview|Top-Level Architecture Overview]]
- [[_COMMUNITY_ChromaDB & Rules Ingestion Docs|ChromaDB & Rules Ingestion Docs]]
- [[_COMMUNITY_Legacy Rules Ingestion Script|Legacy Rules Ingestion Script]]
- [[_COMMUNITY_search_cards Tool & DB Session|search_cards Tool & DB Session]]
- [[_COMMUNITY_Goldfish Phase 3a3b Docs|Goldfish Phase 3a/3b Docs]]
- [[_COMMUNITY_Rules RAG Service|Rules RAG Service]]
- [[_COMMUNITY_Alembic Migration Runner|Alembic Migration Runner]]
- [[_COMMUNITY_Deck Statistics Spec Doc|Deck Statistics Spec Doc]]
- [[_COMMUNITY_Renovate Bot Config|Renovate Bot Config]]
- [[_COMMUNITY_get_current_user Auth Stub|get_current_user Auth Stub]]
- [[_COMMUNITY_Cards Search Route|Cards Search Route]]
- [[_COMMUNITY_User Route Tests|User Route Tests]]
- [[_COMMUNITY_Rules & Glossary Lookup Tools|Rules & Glossary Lookup Tools]]
- [[_COMMUNITY_ADK Agent Factory|ADK Agent Factory]]
- [[_COMMUNITY_Card Route Tests|Card Route Tests]]
- [[_COMMUNITY_Backend Logging Setup|Backend Logging Setup]]
- [[_COMMUNITY_Initial Dev-User Seed Script|Initial Dev-User Seed Script]]
- [[_COMMUNITY_Backend Prestart DB Check|Backend Prestart DB Check]]
- [[_COMMUNITY_Frontend Root TS Config|Frontend Root TS Config]]
- [[_COMMUNITY_GameState Model|GameState Model]]
- [[_COMMUNITY_Ponytail Persona Command|Ponytail Persona Command]]
- [[_COMMUNITY_Auth Login Placeholder Route|Auth Login Placeholder Route]]
- [[_COMMUNITY_binbackend-dev.sh Script|bin/backend-dev.sh Script]]
- [[_COMMUNITY_binbackend-format.sh Script|bin/backend-format.sh Script]]
- [[_COMMUNITY_binbackend-lint.sh Script|bin/backend-lint.sh Script]]
- [[_COMMUNITY_binbackend-test.sh Script|bin/backend-test.sh Script]]
- [[_COMMUNITY_bindev.sh Script|bin/dev.sh Script]]
- [[_COMMUNITY_binfrontend-dev.sh Script|bin/frontend-dev.sh Script]]
- [[_COMMUNITY_binstart-compose.sh Script|bin/start-compose.sh Script]]
- [[_COMMUNITY_Sample Decklist Reference|Sample Decklist Reference]]
- [[_COMMUNITY_Root Renovate Config|Root Renovate Config]]
- [[_COMMUNITY_Renovate GitHub Actions Workflow|Renovate GitHub Actions Workflow]]
- [[_COMMUNITY_backendscriptsdev.sh|backend/scripts/dev.sh]]
- [[_COMMUNITY_backendscriptsformat.sh|backend/scripts/format.sh]]
- [[_COMMUNITY_backendscriptslint.sh|backend/scripts/lint.sh]]
- [[_COMMUNITY_backendscriptstest.sh|backend/scripts/test.sh]]
- [[_COMMUNITY_Rules Embedding Test Script|Rules Embedding Test Script]]
- [[_COMMUNITY_React Logo Asset|React Logo Asset]]
- [[_COMMUNITY_Vite Logo Asset|Vite Logo Asset]]

## God Nodes (most connected - your core abstractions)
1. `User` - 39 edges
2. `Card` - 38 edges
3. `ProcessedChunk` - 37 edges
4. `PipelineContext` - 36 edges
5. `Deck` - 26 edges
6. `ChromaVectorStore` - 23 edges
7. `IngestionDocument` - 22 edges
8. `SectionParser` - 22 edges
9. `ScryfallService` - 21 edges
10. `AsyncClient` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Decision: delete BaseAgent/BaseTool class hierarchy` --RELATES_TO--> `make_agent factory`  [INFERRED]
  PLAN.md → docs/ARCHITECTURE.md
- `Deck Import feature` --DEPENDS_ON--> `Phase 0: Repo cleanup`  [INFERRED]
  docs/DECK_IMPORT_DESIGN.md → PLAN.md
- `AsyncSession` --uses--> `Card`  [INFERRED]
  backend/app/ai/ingestion/scryfall_ingestion.py → backend/app/models/card.py
- `ScryfallService` --uses--> `ScryfallService`  [INFERRED]
  backend/app/services/deck_import.py → backend/app/ai/tools/scryfall.py
- `test_vector_store_search()` --calls--> `ChromaVectorStore`  [INFERRED]
  backend/tests/test_rules_ingestion.py → backend/app/ai/vector_store/chroma.py

## Import Cycles
- 1-file cycle: `backend/app/models/goldfish.py -> backend/app/models/goldfish.py`

## Hyperedges (group relationships)
- **hyperedge_phase1_ship** — feature_phase1_ai_deck_advisor, component_deck_advisor_agent, component_make_agent_factory, component_calculate_stats, component_search_cards_tool [EXTRACTED]
- **hyperedge_phase4_ship** — feature_phase4_scryfall_bulk_ingestion, component_scryfall_bulk_ingestion_script, component_search_cards_tool, decision_tool_db_session_helper, decision_manual_ingestion_scheduling [EXTRACTED]
- **bootstrap_full_pipeline** — bootstrap_command, mtg_architect_command, mtg_backend_command, mtg_frontend_command, mtg_devops_command, mtg_integrations_command, mtg_ai_engineer_command [EXTRACTED]
- **docker_compose_stack** — docker_compose_file, backend_service, db_service, chromadb_service, frontend_service, mtg_network [EXTRACTED]

## Communities (103 total, 22 thin omitted)

### Community 0 - "Scryfall Card Sync"
Cohesion: 0.08
Nodes (68): ScryfallService, AsyncSession, Deck, User, AsyncSession, ScryfallService, User, AsyncSession (+60 more)

### Community 1 - "Backend App Entrypoint"
Cohesion: 0.08
Nodes (27): AsyncClient, AsyncClient, AsyncSession, AsyncClient, AsyncClient, AsyncClient, AsyncSession, test_deck_boards_support() (+19 more)

### Community 2 - "Frontend NPM Dependencies"
Cohesion: 0.05
Nodes (40): dependencies, axios, @emotion/react, @emotion/styled, lucide-react, @mui/icons-material, @mui/material, react (+32 more)

### Community 3 - "Rules Ingestion Parsers"
Cohesion: 0.10
Nodes (24): IngestionDocument, PipelineContext, ProcessedChunk, EmbeddingModel, MtgGlossaryParser, MtgRuleParser, MtgRulesContentSplitter, Downloads content from a web URL. (+16 more)

### Community 4 - "AI Engineer Persona & Docker Stack"
Cohesion: 0.11
Nodes (31): backend/app/ai/adk_agents.py, POST /api/ai/deck/improve, POST /api/ai/deck/suggest, Alembic migrations (upgrade head), ARCHITECTURE.md, backend service, /bootstrap, chromadb-data volume (+23 more)

### Community 5 - "Goldfish Session Schemas"
Cohesion: 0.15
Nodes (27): AsyncSession, User, Deck, GameState, GoldfishActionIn, GoldfishNodeCreate, GoldfishSession, GoldfishSessionCreate (+19 more)

### Community 6 - "Ingestion Pipeline Base Classes"
Cohesion: 0.19
Nodes (17): Any, IngestionDocument, PipelineContext, ProcessedChunk, IngestionDocument, Represents a raw or partially processed document in the ingestion pipeline., Abstract base class for parsing sections into granular chunks (e.g., individual, SectionParser (+9 more)

### Community 7 - "Goldfish Actions Tests"
Cohesion: 0.25
Nodes (23): AsyncClient, _get_root(), _make_deck_with_cards(), _make_deck_with_many_cards(), A deck with two distinct mainboard cards (3x CardA, 1x CardB) plus a     sideboa, 10 copies of a single mainboard card — enough to test a real 7-card     opening, The true "Game start" root (parent_id None) — not just nodes[0], since a     ses, test_action_requires_parent_with_state() (+15 more)

### Community 8 - "RAG Base Interfaces"
Cohesion: 0.12
Nodes (15): ABC, Any, PipelineContext, ProcessedChunk, RAGService, Retrieves relevant text chunks for a given query., Abstract base class for RAG (Retrieval-Augmented Generation) services., EmbeddingModel (+7 more)

### Community 9 - "Frontend App TS Config"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+13 more)

### Community 10 - "Scryfall Bulk Ingestion Script"
Cohesion: 0.17
Nodes (19): Any, AsyncClient, AsyncSession, _card_row(), download_bulk_cards(), fetch_bulk_data_uri(), Looks up the current download URL for a Scryfall bulk-data file. Scryfall     re, Downloads and parses a gzipped-JSONL Scryfall bulk-data file (one print per line (+11 more)

### Community 11 - "Goldfish Playmat & Tree UI"
Cohesion: 0.18
Nodes (12): CardThumb(), GoldfishPlaymat(), GoldfishPlaymatProps, GoldfishTree(), GoldfishTreeProps, NodeTrackerEditor(), NodeTrackerEditorProps, GameState (+4 more)

### Community 12 - "Frontend Node TS Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+11 more)

### Community 13 - "Deck Import Tests"
Cohesion: 0.24
Nodes (17): AsyncClient, User, _card(), _collection_mock(), _create_user(), mock_scryfall(), 'Gnaw to the Bone' appears once in Deck (main) and once in Sideboard     (side), If the collection lookup itself errors (e.g. a transient 429/500), the     whole (+9 more)

### Community 14 - "Chroma Vector Store & Settings"
Cohesion: 0.18
Nodes (10): Any, EmbeddingModel, PipelineContext, ProcessedChunk, BaseSettings, Settings, test_upsert_skips_chunks_without_embeddings(), ChromaVectorStore (+2 more)

### Community 15 - "Deck Stats UI Components"
Cohesion: 0.18
Nodes (12): DeckStats(), StatsData, DeckConstructionGuide(), DeckConstructionGuideProps, DrawProbabilityStats(), DrawProbabilityStatsProps, ColorStats, ManaColorAnalysis() (+4 more)

### Community 16 - "Deck Import Parsing Service"
Cohesion: 0.20
Nodes (14): ScryfallService, parse_decklist(), ParsedDeck, ParsedEntry, Parse a pasted decklist (simple list or MTGA export format) into structured, Resolve parsed entries to Scryfall card IDs via the batch /cards/collection, resolve_entries(), ResolvedEntry (+6 more)

### Community 17 - "AI & Goldfish Schemas"
Cohesion: 0.18
Nodes (12): BaseModel, ScryfallCardPublic, GoldfishActionIn, ChatRequest, ChatResponse, SuggestCardRequest, SuggestCardResponse, CollectionCardCreate (+4 more)

### Community 18 - "Deck Card UI Components"
Cohesion: 0.19
Nodes (12): DeckCard, DeckCardProps, DeckStatsProps, FORMATS, TYPE_ORDER, DeckCard, getCardLimit(), isCardLegal() (+4 more)

### Community 19 - "API Client & Deck List UI"
Cohesion: 0.22
Nodes (10): apiClient, DeckImportModal(), DeckImportModalProps, DeckImportResponse, DeckListItem(), DeckListItemProps, DeckList(), Goldfish() (+2 more)

### Community 20 - "Card & Collection Models"
Cohesion: 0.15
Nodes (3): CardBase, CollectionCard, SQLModel

### Community 21 - "Deck Advisor Chat UI"
Cohesion: 0.20
Nodes (10): ChatBubble(), ChatBubbleProps, Message, ChatInput(), ChatInputProps, DeckAdvisor(), DeckAdvisorProps, Message (+2 more)

### Community 22 - "search_cards Tool Tests"
Cohesion: 0.24
Nodes (9): AsyncSession, Wraps an already-open test AsyncSession as an async context manager,     matchin, _SessionCtx, test_search_cards_falls_back_to_scryfall_when_local_cache_misses(), test_search_cards_formats_results_with_legality(), test_search_cards_hits_local_cache_before_scryfall(), test_search_cards_no_results(), test_search_cards_with_operator_syntax_skips_local_cache() (+1 more)

### Community 23 - "PLAN.md Decisions & Ingestion"
Cohesion: 0.22
Nodes (12): calculate_stats, scryfall_ingestion.py (run_ingestion), search_cards tool, Decision: delete BaseAgent/BaseTool class hierarchy, Decision: manual Scryfall ingestion trigger, no scheduling infra, Decision: stateless tools, deck context in prompt, Decision: dedicated tool-side DB session helper, Decision: collapse single-member uv workspace (+4 more)

### Community 24 - "Deck Builder Search & Hover Hooks"
Cohesion: 0.28
Nodes (8): CollectionCardComponent, CollectionCardProps, DeckBuilderSearch(), useCardHover(), useDebounce(), TYPE_ORDER, DeckBuilder(), CollectionCard

### Community 25 - "Card Hover Context"
Cohesion: 0.26
Nodes (9): DeckBuilderSearchProps, SearchCard, SearchCardProps, CardHoverProvider(), CardHoverContext, CardHoverContextType, DeckStatsDrawOdds, DeckStatsRecommendation (+1 more)

### Community 26 - "Frontend Auth Context"
Cohesion: 0.21
Nodes (9): AuthProvider(), User, AuthContext, AuthContextType, useAuth(), User, MainLayout(), Sidebar() (+1 more)

### Community 27 - "Ingestion Pipeline Types"
Cohesion: 0.26
Nodes (9): PipelineContext, ProcessedChunk, Represents a fully processed chunk of text ready for embedding/indexing., Context object to hold shared state/metadata throughout the pipeline execution., PipelineContext, ProcessedChunk, PipelineContext, ProcessedChunk (+1 more)

### Community 28 - "ScryfallService Client"
Cohesion: 0.26
Nodes (5): Any, AsyncClient, get_scryfall_service(), Batch lookup by arbitrary identifiers (name, or set+collector_number).         S, ScryfallService

### Community 29 - "Deck Import Feature & Auth Docs"
Cohesion: 0.23
Nodes (9): POST /api/v1/decks/import, DeckImportModal, deck_import.py service, get_current_user (dev-mode stub), User model, Decision: best-effort deck import with inline replace path, Google OAuth authentication, Deck Import feature (+1 more)

### Community 30 - "Frontend Pages & Card Hover Preview"
Cohesion: 0.21
Nodes (6): CardHoverPreview(), Collection(), GoldfishSessionPage(), LandingPage(), queryClient, theme

### Community 31 - "GoldfishNode/Session Models"
Cohesion: 0.24
Nodes (11): datetime, GoldfishNode, GoldfishNodeBase, GoldfishNodeCreate, GoldfishNodePublic, GoldfishSession, GoldfishSessionBase, GoldfishSessionCreate (+3 more)

### Community 32 - "Deck Stats Calculation Service"
Cohesion: 0.33
Nodes (9): Any, Deck, _calculate_cmc(), _calculate_color_needs(), _calculate_draw_odds(), calculate_stats(), Calculate pip counts, source counts, and recommended sources based on Karsten's, Calculate hypergeometric probabilities for drawing lands.     P(X=k) = C(K, k) * (+1 more)

### Community 33 - "AI Suggest/Chat Route Tests"
Cohesion: 0.31
Nodes (8): AsyncClient, _fake_run_async_returning(), The deck's format is threaded into the agent context so it can filter     sugges, test_ai_chat(), test_ai_suggest(), test_ai_suggest_deck_not_found(), test_ai_suggest_rejects_deck_owned_by_another_user(), test_ai_suggest_respects_format_legality_context()

### Community 34 - "AI Module Architecture Docs"
Cohesion: 0.33
Nodes (9): agents/ module, AI module (backend/app/ai), make_agent factory, rag/ module, rules_agent, RulesRAG, tools/ module, types.py (+1 more)

### Community 35 - "Top-Level Architecture Overview"
Cohesion: 0.24
Nodes (10): Alembic migrations, Backend (FastAPI service), deck_advisor_agent, Frontend (React/TS/Vite app), src/main.tsx, ScryfallService, backend/README.md, frontend/index.html (+2 more)

### Community 36 - "ChromaDB & Rules Ingestion Docs"
Cohesion: 0.24
Nodes (7): ChromaDB vector store, docker-compose.yml, ingestion/ module, rules_ingestion.py, vector_store/ module, Fix: mtg-chromadb healthcheck via /dev/tcp, Rulings Agent (FAISS/numpy design)

### Community 37 - "Legacy Rules Ingestion Script"
Cohesion: 0.22
Nodes (7): DocEmbeddingFunction, download_rules(), ingest_rules(), parse_rules(), Downloads the comprehensive rules text., Parses rules into chunks., Embeds rules and saves to ChromaDB.

### Community 38 - "search_cards Tool & DB Session"
Cohesion: 0.31
Nodes (7): AsyncSession, _card_to_dict(), _format_card(), Searches for cards matching a query (Scryfall search syntax). Plain name     que, search_cards(), _search_local(), get_tool_session()

### Community 39 - "Goldfish Phase 3a/3b Docs"
Cohesion: 0.22
Nodes (9): GoldfishNode model, GoldfishPlaymat.tsx, goldfish API router, GoldfishSession model, GoldfishTree.tsx, Decision: life_total stays first-class on state, not trackers, Phase 3a: Manual action log + branching tree, Phase 3b: Assisted simulator (+1 more)

### Community 40 - "Rules RAG Service"
Cohesion: 0.29
Nodes (4): Retrieval-Augmented Generation for MTG Rules., Retrieves top-k relevant rules for the query.         Returns a list of rule tex, Retrieves glossary definitions for a term., RulesRAG

### Community 41 - "Alembic Migration Runner"
Cohesion: 0.33
Nodes (4): Run migrations in 'offline' mode.      This configures the context with just a U, Run migrations in 'online' mode.      In this scenario we need to create an Engi, run_migrations_offline(), run_migrations_online()

### Community 42 - "Deck Statistics Spec Doc"
Cohesion: 0.33
Nodes (5): Color Distribution (pips vs sources), Draw Probability (Hypergeometric), Karsten's Heuristic, Mana Curve, Deck Statistics feature

### Community 43 - "Renovate Bot Config"
Cohesion: 0.33
Nodes (5): extends, ignorePaths, packageRules, prHourlyLimit, timezone

### Community 44 - "get_current_user Auth Stub"
Cohesion: 0.40
Nodes (4): get_current_user(), Get the current user.          NOTE: This is a SIMPLIFIED implementation for dev, AsyncSession, User

### Community 45 - "Cards Search Route"
Cohesion: 0.50
Nodes (4): ScryfallService, get_card(), Search for cards using Scryfall., search_cards()

### Community 46 - "User Route Tests"
Cohesion: 0.50
Nodes (4): AsyncClient, AsyncSession, test_create_user(), test_read_user_me()

### Community 47 - "Rules & Glossary Lookup Tools"
Cohesion: 0.40
Nodes (4): lookup_glossary_term(), query_comprehensive_rules(), Looks up a term in the Magic: The Gathering Glossary., Searches the Magic: The Gathering Comprehensive Rules for relevant sections.

### Community 48 - "ADK Agent Factory"
Cohesion: 0.50
Nodes (3): Agent, make_agent(), Thin factory for this codebase's ADK Agent instances: Gemini model from     sett

### Community 49 - "Card Route Tests"
Cohesion: 0.67
Nodes (3): AsyncClient, test_get_card_by_id(), test_search_cards()

### Community 50 - "Backend Logging Setup"
Cohesion: 0.50
Nodes (3): Configures and returns a logger with a standard format., setup_logging(), Logger

### Community 55 - "Ponytail Persona Command"
Cohesion: 0.67
Nodes (3): /ponytail, Ponytail intensity levels (lite/full/ultra), Ponytail YAGNI ladder

## Knowledge Gaps
- **160 isolated node(s):** `extends`, `packageRules`, `prHourlyLimit`, `timezone`, `ignorePaths` (+155 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Scryfall Card Sync` to `AI Suggest/Chat Route Tests`, `Backend App Entrypoint`, `Goldfish Session Schemas`, `Goldfish Actions Tests`, `get_current_user Auth Stub`, `Deck Import Tests`, `Card & Collection Models`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `ProcessedChunk` connect `Ingestion Pipeline Types` to `Rules Ingestion Parsers`, `Ingestion Pipeline Base Classes`, `RAG Base Interfaces`, `Rules RAG Service`, `Chroma Vector Store & Settings`, `AI & Goldfish Schemas`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `Card` connect `Scryfall Card Sync` to `Backend App Entrypoint`, `Goldfish Session Schemas`, `Goldfish Actions Tests`, `Scryfall Bulk Ingestion Script`, `AI & Goldfish Schemas`, `Card & Collection Models`, `search_cards Tool Tests`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `User` (e.g. with `AsyncSession` and `User`) actually correct?**
  _`User` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `Card` (e.g. with `Any` and `AsyncClient`) actually correct?**
  _`Card` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 34 inferred relationships involving `ProcessedChunk` (e.g. with `PipelineContext` and `ProcessedChunk`) actually correct?**
  _`ProcessedChunk` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `PipelineContext` (e.g. with `PipelineContext` and `ProcessedChunk`) actually correct?**
  _`PipelineContext` has 33 INFERRED edges - model-reasoned connections that need verification._