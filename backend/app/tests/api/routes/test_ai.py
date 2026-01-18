import pytest
from app.core.config import settings
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_suggest(client: AsyncClient) -> None:
    data = {"deck_context": ["Black Lotus"], "query": "Suggest something expensive"}
    response = await client.post(f"{settings.API_V1_STR}/ai/suggest", json=data)
    assert response.status_code == 200
    assert "message" in response.json()

@pytest.mark.asyncio
async def test_ai_chat(client: AsyncClient) -> None:
    response = await client.post(f"{settings.API_V1_STR}/ai/chat")
    assert response.status_code == 200
    assert response.json() == {"message": "AI chat placeholder"}
