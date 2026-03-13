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
- `bin/`: Helper utility scripts for development and orchestration.
- `docs/`: Architecture diagrams, technical specifications, and design documents.
- `references/`: Essential reference materials, like the Magic: The Gathering comprehensive rules.
- `.agent/`: Workflows and instructions for the Google Agent Development Kit framework.
- `backups/`: Database backups and snapshot points.

## 🛠️ Utility Scripts

The project includes several helper scripts in the `bin/` directory to simplify common tasks:

- **Full Stack:**
  - `./bin/start-compose.sh`: Start the entire application using Docker Compose.
  - `./bin/dev.sh`: Centralized script for various dev workflows.
- **Backend:**
  - `./bin/backend-dev.sh`: Start the backend development server.
  - `./bin/backend-test.sh`: Run backend tests.
  - `./bin/backend-lint.sh`: Run linter (Ruff) on backend code.
  - `./bin/backend-format.sh`: Format backend code.
- **Frontend:**
  - `./bin/frontend-dev.sh`: Start the frontend development server.

## 🔑 Key Features

- **Live Scryfall Search:** Proxy API to fetch real card data directly from Scryfall.
- **Deck Management:** Create, read, and manage MTG decks (persisted in SQLite).
- **Async Implementation:** Full async/await stack for high performance.
- **AI Suggestions:** Built-in hooks for AI-powered deck building (experimental).