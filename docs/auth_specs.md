# Authentication Architecture & Implementation Guide

This document outlines the architecture for Google OAuth implementation and assigns tasks to specific agent workflows.

## Architecture Overview

We will use **Google OAuth 2.0** for authentication.
1.  **Frontend**: Uses Google Identity Services SDK to sign in the user and obtain an `id_token`.
2.  **Backend**: Receives the `id_token`, verifies it with Google, creates/updates the local `User` record, and issues a backend-specific **access token** (JWT) for subsequent API requests.

## Workflow Assignments

### 1. Google Project Setup
**Agent**: [`/mtg-integrations`](#mtg-integrations)
*   [ ] Create/Configure Google Cloud Project.
*   [ ] Configure OAuth Consent Screen.
*   [ ] Create OAuth 2.0 Client ID (Web Application).
*   [ ] Add authorized origins (`http://localhost:3000`, `http://localhost:5173`).
*   [ ] Securely store `GOOGLE_CLIENT_ID` in `frontend/.env` and `backend/.env`.

### 2. Backend Implementation
**Agent**: [`/mtg-backend`](#mtg-backend)
*   [ ] **Dependency**: Install `google-auth` and `pyjwt` (or `python-jose`).
*   [ ] **Model**: Ensure `User` model exists (email, google_id, avatar_url).
*   [ ] **Service**: Create `AuthService` to:
    *   Verify Google ID Token.
    *   Get_or_create user from payload.
    *   Create Session JWT.
*   [ ] **API**: Implement endpoints:
    *   `POST /api/auth/login`: Accepts `{ id_token: str }`, returns `{ access_token: str, token_type: "bearer" }`.
    *   `GET /api/users/me`: Returns current user profile (protected dependency).

### 3. Frontend Implementation
**Agent**: [`/mtg-frontend`](#mtg-frontend)
*   [ ] **Package**: Install `@react-oauth/google`.
*   [ ] **Provider**: Wrap app in `GoogleOAuthProvider`.
*   [ ] **Component**: Create `LoginButton` component.
*   [ ] **State**: Add AuthContext/Zustand store to manage `user` and `accessToken`.
*   [ ] **Flow**:
    *   On Google Success -> `POST /api/auth/login`.
    *   On Response -> Store Token -> Fetch User Profile.
    *   Add `Authorization: Bearer <token>` to `apiClient` interceptors.

## Data Models

### User (Backend)
```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    google_id: str = Field(index=True, unique=True)
    full_name: str | None = None
    picture: str | None = None
    is_active: bool = True
```

### API Contract

**POST /api/auth/login**
Request:
```json
{
  "id_token": "eyJhbGci..."
}
```
Response:
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```
