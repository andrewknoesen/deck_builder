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
    # Note: This is currently a placeholder in the API
    response = await client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 200
    assert response.json() == {"message": "User me endpoint placeholder"}
