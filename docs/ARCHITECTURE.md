# MTG Deck Builder - Architecture Design

## 1. Architecture Overview

The system is a containerized web application designed to help users build and manage Magic: The Gathering decks.

- **Frontend**: A React application (TypeScript) serving as the UI. It handles authentication state, deck building interactions, and stats visualization. It leverages `react-query` or similar for state management and caching Scryfall/local API responses.
- **Backend API**: A Python FastAPI service acting as the single source of truth for user decks and user data. It proxies or orchestrates calls to Scryfall for card data to avoid direct heavy lifting on the client, or simply validates card IDs stored in decks.
- **Database**: The backend is designed to be database-agnostic but will start with a persistent SQL store (SQLite/Postgres) to save User and Deck relationships.
- **Data Source**: Scryfall API is the authority for Card data. Our backend only stores card identifiers (Scryfall IDs) and metadata (quantities, board location) within decks, fetching full card details on demand or caching them.
- **Authentication**: Google OAuth via the Google SDK on the frontend. ID tokens are sent to the backend, which verifies them and manages the user session/user creation.

## 2. Directory Structure

```text
/
├── docker-compose.yml          # Orchestration for all services
├── .env.example                # Template for environment variables
├── /frontend                   # React Application
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── /src
│   │   ├── /components         # Reusable UI components
│   │   ├── /pages              # Page views
│   │   ├── /api                # API client layer
│   │   ├── /hooks              # Custom hooks (e.g. useAuth, useDeck)
│   │   └── /types              # Shared TypeScript interfaces
│   └── /public
├── /backend                    # FastAPI Application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── /app
│   │   ├── main.py             # Entry point
│   │   ├── /api                # Route handlers (v1/)
│   │   ├── /core               # Config, security, database objects
│   │   ├── /models             # Pydantic models & SQLAlchemy models
│   │   ├── /services           # Business logic (Scryfall, Deck ops)
│   │   └── /tests              # Pytest suite
└── /infra                      # Infrastructure configurations (Nginx, etc. if needed)
```

## 3. API Design

Base URL: `/api/v1`

### Authentication
- `POST /api/v1/auth/login`: Accepts Google ID token. Returns access token (or sets session cookie) and user info.
- `GET /api/v1/users/me`: Returns current user profile.

### Cards (Proxy/Cache Scryfall)
- `GET /api/v1/cards/search?q={query}`: Proxy to Scryfall search or local cache.
- `GET /api/v1/cards/{id}`: Get detailed card info.

### Decks
- `GET /api/v1/decks`: List user's decks.
- `POST /api/v1/decks`: Create a new deck. Body: `{ name: string, format: string }`.
- `GET /api/v1/decks/{id}`: Get full deck details including cards.
- `PUT /api/v1/decks/{id}`: Update deck metadata.
- `DELETE /api/v1/decks/{id}`: Delete a deck.

### Deck Cards
- `POST /api/v1/decks/{id}/cards`: Add card to deck. Body: `{ scryfall_id: string, quantity: int, board: 'main'|'side' }`.
- `PUT /api/v1/decks/{id}/cards/{card_id}`: Update quantity/board.
- `DELETE /api/v1/decks/{id}/cards/{card_id}`: Remove card.

### AI Assistant
- `POST /api/v1/ai/suggest`: Get card suggestions. Body: `{ deck_context: [...], query: string }`.
- `POST /api/v1/ai/chat`: Simple chat interface for deck building advice.

## 4. Agent Task Allocation

### 1. DevOps Agent (Priority: High)
- [ ] Create root `docker-compose.yml`.
- [ ] Create `frontend/Dockerfile` (React + Nginx/Node).
- [ ] Create `backend/Dockerfile` (Python 3.11+).
- [ ] Ensure hot-reloading works for local development.

### 2. Backend Agent (Priority: High)
- [ ] Initialize FastAPI project structure.
- [ ] Implement `User` and `Deck` SQLAlchemy models.
- [ ] Create Pydantic schemas for API requests/responses.
- [ ] Implement Google ID Token verification middleware.
- [ ] Build CRUD endpoints for Decks.
- [ ] Implement Scryfall integration service.
- [ ] Implement AI Service (LLM integration).

### 3. Frontend Agent (Priority: Medium)
- [ ] Initialize React + TypeScript + Vite project.
- [ ] Setup API client (axios/fetch) with interceptors for auth.
- [ ] Implement Google Login button and auth context.
- [ ] Create Deck List view.
- [ ] Create Deck Builder view (Search pane + Deck pane).
- [ ] Implement Mana Curve visualization.

### 4. Integrations Agent (Priority: Low)
- [ ] Refine Scryfall search (filters, sorting).
- [ ] Add Pricing API integration.
- [ ] Enhance Auth flow (refresh tokens, profile pictures).
