import pytest
from app.core.config import settings
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, db_session: AsyncSession) -> None:
    user_data = {
        "email": "newuser@example.com",
        "google_sub": "sub123",
        "full_name": "New User"
    }
    response = await client.post(f"{settings.API_V1_STR}/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["google_sub"] == "sub123"
    assert "id" in data

@pytest.mark.asyncio
async def test_read_user_me(client: AsyncClient) -> None:
    # get_current_user is a dev-mode stub: with no users in the DB it creates
    # and returns a default dev user.
    response = await client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "dev@example.com"
    assert data["google_sub"] == "dev_sub_12345"
