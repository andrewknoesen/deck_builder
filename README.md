# MTG Deck Builder

A modern Magic: The Gathering deck-building application featuring Scryfall integration, AI-powered suggestions, and a robust FastAPI backend.

## 🚀 Tech Stack

### Backend
- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Database:** [SQLModel](https://sqlmodel.tiangolo.com/) (SQLAlchemy + Pydantic)
- **Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
- **Package Manager:** [uv](https://github.com/astral-sh/uv)
- **Primary Data Source:** [Scryfall API](https://scryfall.com/docs/api)

### Frontend
- **Framework:** [React](https://reactjs.org/) with [TypeScript](https://www.typescriptlang.org/)
- **Build Tool:** [Vite](https://vitejs.dev/)

### Infrastructure
- **Containerization:** [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)

## 🛠️ Getting Started

### Prerequisites
- Docker and Docker Compose installed.

### Setup & Run
1. Clone the repository.
2. Spin up the entire stack:
   ```bash
   docker-compose up --build
   ```
3. The application will be available at:
   - Frontend: [http://localhost:5173](http://localhost:5173)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - API Docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

## 🧪 Testing

The backend includes a comprehensive test suite using `pytest` and `pytest-asyncio`, with a dedicated async SQLite test database.

To run the backend tests locally (assuming `uv` is installed):
```bash
cd backend
uv run pytest
```

## 🏗️ Project Structure

- `backend/`: FastAPI application, models, and Scryfall services.
- `frontend/`: React frontend with modern UI components.
- `docker-compose.yml`: Orchestrates the backend, frontend, and database volumes.
- `scripts/`: Helper scripts for development and orchestration.

## 🛠️ Utility Scripts

The project includes several helper scripts in the `scripts/` directory to simplify common tasks:

- **Full Stack:**
  - `./scripts/start-compose.sh`: Start the entire application using Docker Compose.
- **Backend:**
  - `./scripts/backend-dev.sh`: Start the backend development server.
  - `./scripts/backend-test.sh`: Run backend tests.
  - `./scripts/backend-lint.sh`: Run linter (Ruff) on backend code.
  - `./scripts/backend-format.sh`: Format backend code.
- **Frontend:**
  - `./scripts/frontend-dev.sh`: Start the frontend development server.

## 🔑 Key Features

- **Live Scryfall Search:** Proxy API to fetch real card data directly from Scryfall.
- **Deck Management:** Create, read, and manage MTG decks (persisted in SQLite).
- **Async Implementation:** Full async/await stack for high performance.
- **AI Suggestions:** Built-in hooks for AI-powered deck building (experimental).