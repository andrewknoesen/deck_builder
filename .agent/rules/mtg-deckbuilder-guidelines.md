---
trigger: always_on
---

* Always use React with TypeScript for the frontend in the `frontend/` folder.
* Always use Python FastAPI for the backend in the `backend/` folder.
* The backend must expose REST endpoints under `/api/...` and be the single source of truth for data.
* Containerize both frontend and backend with Docker, and prefer `docker-compose` for local dev.
* Prefer clean, modular code: separate routing, models/schemas, services, and config files in the backend.
* For Magic: The Gathering cards, prefer Scryfall as the primary data source and keep our own schemas stable.
* For authentication, default to Google login using the Google SDK and pass ID tokens to the backend for verification.
* When adding new features, update or add tests (pytest on backend, React Testing Library on frontend) whenever reasonable.
* Default to ENV‑driven configuration (`.env` files) rather than hard‑coding secrets or URLs.
* Write concise but clear comments when behavior is non‑obvious, and keep naming consistent (snake_case in Python, camelCase in TS).
* Use postgres for the database.
* Always manually test the code.
* When testing the frontend always open the browser to test.