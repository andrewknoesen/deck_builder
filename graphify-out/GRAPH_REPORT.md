# Graph Report - deck_builder  (2026-07-07)

## Corpus Check
- 142 files · ~289,475 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 772 nodes · 1132 edges · 89 communities (73 shown, 16 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 203 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1acca7fe`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 63|Community 63]]

## God Nodes (most connected - your core abstractions)
1. `ProcessedChunk` - 39 edges
2. `PipelineContext` - 38 edges
3. `Card` - 31 edges
4. `ChromaVectorStore` - 22 edges
5. `compilerOptions` - 20 edges
6. `SentenceTransformerEmbedder` - 18 edges
7. `compilerOptions` - 18 edges
8. `User` - 17 edges
9. `AsyncSession` - 15 edges
10. `ScryfallService` - 14 edges

## Surprising Connections (you probably didn't know these)
- `AsyncClient` --uses--> `User`  [INFERRED]
  backend/app/tests/api/routes/test_legalities.py → backend/app/models/user.py
- `WebSource` --uses--> `PipelineContext`  [INFERRED]
  backend/app/ai/ingestion/rules_ingestion.py → backend/app/ai/types.py
- `WebSource` --uses--> `ProcessedChunk`  [INFERRED]
  backend/app/ai/ingestion/rules_ingestion.py → backend/app/ai/types.py
- `test_web_source_load()` --calls--> `WebSource`  [INFERRED]
  backend/tests/test_rules_ingestion.py → backend/app/ai/ingestion/rules_ingestion.py
- `PipelineContext` --uses--> `PipelineContext`  [INFERRED]
  backend/app/ai/ingestion/rules_ingestion.py → backend/app/ai/types.py

## Import Cycles
- 1-file cycle: `backend/app/ai/agents/rules/__init__.py -> backend/app/ai/agents/rules/__init__.py`

## Communities (89 total, 16 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (54): ABC, PipelineContext, ProcessedChunk, Represents a fully processed chunk of text ready for embedding/indexing., Context object to hold shared state/metadata throughout the pipeline execution., PipelineContext, ProcessedChunk, Any (+46 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (41): create_initial_data(), main(), AsyncSession, ScryfallService, Any, AsyncClient, AsyncClient, Deck (+33 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (30): IngestionDocument, PipelineContext, ProcessedChunk, EmbeddingModel, MtgGlossaryParser, MtgRuleParser, MtgRulesContentSplitter, Parses the 'Rules' section into individual rules. (+22 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (35): get_current_user(), Get the current user.          NOTE: This is a SIMPLIFIED implementation for dev, ScryfallService, AsyncSession, User, ScryfallService, AsyncSession, ScryfallService (+27 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (39): dependencies, axios, @emotion/react, @emotion/styled, lucide-react, @mui/icons-material, @mui/material, react (+31 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (27): 1. Mana Curve, 2. Color Distribution (Pip Count vs. Sources), 3. Land Count Recommendations, 4. Draw Probability (Hypergeometric Distribution), 5. Proposed Backend Implementation, A. Colored Pips (Requirements), Algorithm, Algorithm (+19 more)

### Community 6 - "Community 6"
Cohesion: 0.10
Nodes (13): BaseAgent, BaseTool, Whatever shared stuff tools need (clients, config, etc.)., Base class for all tools an agent can use., Stable identifier used by the agent/LLM., Execute the tool with model-provided args., Base class for agents bound to a specific tool family., The prompt for the agent. (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+13 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (12): AuthContext, AuthContextType, AuthProvider(), useAuth(), User, MainLayout(), Sidebar(), SidebarProps (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+11 more)

### Community 10 - "Community 10"
Cohesion: 0.11
Nodes (6): AsyncClient, AsyncClient, AsyncSession, test_legalities_sync(), client(), db_session()

### Community 11 - "Community 11"
Cohesion: 0.18
Nodes (12): DeckStats(), StatsData, DeckConstructionGuide(), DeckConstructionGuideProps, DrawProbabilityStats(), DrawProbabilityStatsProps, ColorStats, ManaColorAnalysis() (+4 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (16): 1. Architecture Overview, 2. Implementation Plan, 3. Security & Deployment, Agent Definition (`backend/app/ai/agents.py`), AI Architecture - Deck Advisor Chat, API Routes (`backend/app/api/routes/ai.py`), Components, Components (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.20
Nodes (13): BaseModel, ChatRequest, ScryfallCardPublic, chat_assistant(), Get card suggestions based on deck context and user query., Chat with the Rules Agent., suggest_cards(), SuggestCardRequest (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.23
Nodes (11): CardHoverPreview(), DeckBuilderSearch(), DeckBuilderSearchProps, SearchCard, SearchCardProps, CardHoverContext, CardHoverContextType, CardHoverProvider() (+3 more)

### Community 15 - "Community 15"
Cohesion: 0.19
Nodes (12): DeckCard, DeckCardProps, DeckStatsProps, FORMATS, TYPE_ORDER, DeckCard, getCardLimit(), isCardLegal() (+4 more)

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (14): 1. Architecture Overview, 1. DevOps Agent (Priority: High), 2. Backend Agent (Priority: High), 2. Directory Structure, 3. API Design, 3. Frontend Agent (Priority: Medium), 4. Agent Task Allocation, 4. Integrations Agent (Priority: Low) (+6 more)

### Community 17 - "Community 17"
Cohesion: 0.14
Nodes (13): 1. Feature Overview, 2. Frontend Design, 3. Backend Design, 4. Task Breakdown, API Endpoint, Backend Agent, Component: `DeckImportModal`, Deck Import Feature Design (+5 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (13): 1. Overview, 2.1. Knowledge Base, 2.2. The Pipeline, 2. Architecture & Data Strategy (Cost-Optimized), 3. Workflow & Task Order, 4. Implementation Details for @[/mtg-ai-engineer], AI Rulings Agent Design, Cost Control (+5 more)

### Community 19 - "Community 19"
Cohesion: 0.15
Nodes (12): Backend, Frontend, 🛠️ Getting Started, Infrastructure, 🔑 Key Features, MTG Deck Builder, Prerequisites, 🏗️ Project Structure (+4 more)

### Community 20 - "Community 20"
Cohesion: 0.24
Nodes (7): ChatBubble(), ChatBubbleProps, Message, ChatInput(), ChatInputProps, AgentChat(), Message

### Community 21 - "Community 21"
Cohesion: 0.20
Nodes (9): 1. `types.py`, 2. `vector_store/`, 3. `ingestion/`, 4. `rag/`, 5. `agents/`, 6. `tools/`, AI Module Documentation, Development Guidelines (+1 more)

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (6): apiClient, CollectionCardComponent, CollectionCardProps, Collection(), TYPE_ORDER, CollectionCard

### Community 23 - "Community 23"
Cohesion: 0.31
Nodes (4): Any, AsyncClient, get_scryfall_service(), ScryfallService

### Community 24 - "Community 24"
Cohesion: 0.20
Nodes (9): 1. Google Project Setup, 2. Backend Implementation, 3. Frontend Implementation, API Contract, Architecture Overview, Authentication Architecture & Implementation Guide, Data Models, User (Backend) (+1 more)

### Community 25 - "Community 25"
Cohesion: 0.20
Nodes (9): 1. File Reader, 2. Content Type Splitter, 3. Rule Parser, 4. Embedding, 5. Storage (ChromaDB), Architecture Overview, detailed Components, MTG Rules Ingestion Pipeline Design (+1 more)

### Community 26 - "Community 26"
Cohesion: 0.22
Nodes (7): DocEmbeddingFunction, download_rules(), ingest_rules(), parse_rules(), Downloads the comprehensive rules text., Parses rules into chunks., Embeds rules and saves to ChromaDB.

### Community 27 - "Community 27"
Cohesion: 0.22
Nodes (8): Database Migrations, Features, 🛠️ Helper Scripts, Initial Setup, MTG Deck Builder Backend, Path to Development, Running Tests, Running the API

### Community 28 - "Community 28"
Cohesion: 0.22
Nodes (8): Agent Layer, Architecture, deck_builder, Dev Setup, graphify, Key Conventions, Skills, Tech Stack

### Community 29 - "Community 29"
Cohesion: 0.22
Nodes (8): Boundaries, Intensity, Output, Persistence, Ponytail, Rules, The ladder, When NOT to be lazy

### Community 30 - "Community 30"
Cohesion: 0.36
Nodes (6): DeckListItem(), DeckListItemProps, DeckList(), Deck, DeckStatsDrawOdds, DeckStatsRecommendation

### Community 31 - "Community 31"
Cohesion: 0.22
Nodes (8): 1. Setup Data Directory, 2. Create Parsing Logic (`backend/app/ai/ingestion/rules_parser.py`), 3. Implement Embeddings & Storage (`backend/app/ai/ingestion/rules_ingestion.py`), Implementation Guide: MTG Rules Ingestion Pipeline, Next Steps, Prerequisites, Step-by-Step Implementation, Verification Scenarios

### Community 32 - "Community 32"
Cohesion: 0.33
Nodes (4): Run migrations in 'offline' mode.      This configures the context with just a U, Run migrations in 'online' mode.      In this scenario we need to create an Engi, run_migrations_offline(), run_migrations_online()

### Community 33 - "Community 33"
Cohesion: 0.33
Nodes (5): extends, ignorePaths, packageRules, prHourlyLimit, timezone

### Community 34 - "Community 34"
Cohesion: 0.50
Nodes (4): AsyncClient, AsyncSession, test_create_user(), test_read_user_me()

### Community 35 - "Community 35"
Cohesion: 0.40
Nodes (4): lookup_glossary_term(), query_comprehensive_rules(), Looks up a term in the Magic: The Gathering Glossary., Searches the Magic: The Gathering Comprehensive Rules for relevant sections.

### Community 36 - "Community 36"
Cohesion: 0.67
Nodes (3): AsyncClient, test_ai_chat(), test_ai_suggest()

### Community 37 - "Community 37"
Cohesion: 0.67
Nodes (3): AsyncClient, test_get_card_by_id(), test_search_cards()

### Community 38 - "Community 38"
Cohesion: 0.50
Nodes (3): Configures and returns a logger with a standard format., setup_logging(), Logger

### Community 39 - "Community 39"
Cohesion: 0.50
Nodes (3): Expanding the ESLint configuration, React Compiler, React + TypeScript + Vite

## Knowledge Gaps
- **233 isolated node(s):** `extends`, `packageRules`, `prHourlyLimit`, `timezone`, `ignorePaths` (+228 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ScryfallCardPublic` connect `Community 13` to `Community 1`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `ProcessedChunk` connect `Community 0` to `Community 2`, `Community 13`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `Card` connect `Community 1` to `Community 3`, `Community 13`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 36 inferred relationships involving `ProcessedChunk` (e.g. with `PipelineContext` and `ProcessedChunk`) actually correct?**
  _`ProcessedChunk` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `PipelineContext` (e.g. with `PipelineContext` and `ProcessedChunk`) actually correct?**
  _`PipelineContext` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `Card` (e.g. with `AsyncSession` and `ScryfallService`) actually correct?**
  _`Card` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `ChromaVectorStore` (e.g. with `IngestionDocument` and `PipelineContext`) actually correct?**
  _`ChromaVectorStore` has 15 INFERRED edges - model-reasoned connections that need verification._