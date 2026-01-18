# MTG Deck Builder Backend

FastAPI backend for the MTG Deck Builder app.

## Features
- **Scryfall Integration:** Real-time card search and retrieval via `app/services/scryfall.py`.
- **Database:** PostgreSQL (with `asyncpg`) using `SQLModel` for full async operations.
- **Migrations:** Managed by Alembic.
- **API Versioning:** All routes follow `/api/v1/...` prefix.
- **Robust Testing:** 100% async testing with `pytest` and `httpx.AsyncClient`.

## Path to Development

### Initial Setup
1. Install `uv`:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Sync dependencies:
   ```bash
   uv sync
   ```

### Database Migrations
Create a new migration:
```bash
uv run alembic revision --autogenerate -m "description"
```
Apply migrations:
```bash
uv run alembic upgrade head
```

### Running Tests
All tests are located in `app/tests/`. To run them:
```bash
uv run pytest
```

### Running the API
```bash
uv run uvicorn app.main:app --reload
```

## 🛠️ Helper Scripts

The `backend/scripts/` directory contains convenient wrappers for common development commands:

- `./scripts/dev.sh`: Start the development server.
- `./scripts/test.sh`: Run the test suite.
- `./scripts/lint.sh`: Run linting checks (Ruff).
- `./scripts/format.sh`: Automatically format the codebase.
