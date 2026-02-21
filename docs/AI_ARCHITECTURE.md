# AI Architecture - Deck Advisor Chat

This document outlines the architecture and implementation plan for the AI Chat Feature, which integrates Google's Agent Development Kit (ADK) into the MTG Deck Builder.

## 1. Architecture Overview

The feature introduces a conversational AI agent embedded in the Deck Builder interface. This agent has access to card data and deck context to provide meaningful recommendations.

### Components
- **AI Agent (Backend)**: Built with Google ADK, running within the FastAPI service.
- **Tools**: Specialized functions (`search_cards`, `get_deck_stats`) that the agent can call.
- **API Layer**: New endpoints in FastAPI to relay messages between the frontend and the agent.
- **UI (Frontend)**: A chat widget in the React application.

## 2. Implementation Plan

### Phase 1: AI Engineer Tasks (ADK Integration)

**Goal**: scalable, tool-enabled agent that understands Magic: The Gathering context.

#### Dependencies
- Add `google-cloud-aiplatform[agent_engines]` (or equivalent ADK implementation) to `backend/pyproject.toml`.

#### Configuration
- New `backend/app/ai/config.py` handling `gemini-2.0-flash`, `GOOGLE_API_KEY`, etc.

#### Agent Definition (`backend/app/ai/agents.py`)
- Initialize `DeckAdvisorAgent`.
- System Prompt: "You are an expert MTG deck builder helping a user refine their deck..."
- Context Management: The agent needs to receive the current deck list as context for each turn or session.

#### Tools (`backend/app/ai/tools.py`)
- `search_cards(query: str) -> List[Card]`: Wraps existing Scryfall service logic.
- `get_deck_stats(deck_list: List[str]) -> Dict`: Returns mana curve, color distribution.
- `check_legality(card_name: str, format: str) -> bool`: Verifies format legality.

### Phase 2: Backend Engineer Tasks (API & Data)

**Goal**: Expose the agent via REST and provide user context.

#### Environment Variables
- `GOOGLE_API_KEY`: API Key for Google Gen AI (Vertex AI) access.
- `GOOGLE_PROJECT_ID`: (Optional if API Key covers it, but good to have)
- `GOOGLE_LOCATION`: Region for Vertex AI.
- `AI_MODEL_NAME`: e.g., `gemini-2.0-flash`

#### API Routes (`backend/app/api/routes/ai.py`)
- `POST /api/v1/ai/chat`
  - **Payload**: `{ "message": "string", "deck_id": 123 }`
  - **Response**: `{ "text": "...", "suggestions": [...] }`
- **Logic**:
  1. Fetch Deck from DB using `deck_id`.
  2. Serialize deck into a context string (e.g., "Current Deck: [Card A, Card B...]").
  3. Invoke Agent with user message + context.
  4. Return agent response.

### Phase 3: Frontend Engineer Tasks (UI/UX)

**Goal**: Non-intrusive, helpful chat interface.

#### Components
- **DeckChatWidget**: A collapsible chat window in the bottom-right or a sidebar panel.
  - Displays message history.
  - Handles "typing" states.
  - Renders card suggestions as clickable links or "Add" buttons.

#### Store/State
- Use `react-query` mutations to send messages.
- seamless updates to the Deck List when the AI adds cards (if supported) or when user approves a suggestion.

## 3. Security & Deployment

- **Auth**: The `/ai/chat` endpoint must be protected behind the existing `deps.get_current_user` dependency.
- **Docker**: The backend Dockerfile needs to support the new Google Cloud dependencies. Pass `GOOGLE_API_KEY` via environment variables.
