import pytest
from app.core.config import settings
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_cards(client: AsyncClient) -> None:
    # Use a query that is very likely to return Black Lotus
    response = await client.get(
        f'{settings.API_V1_STR}/cards/search?q=name:"Black Lotus"'
    )
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert len(content["data"]) > 0
    # Any version of Black Lotus should have the correct name
    assert any("Black Lotus" in card["name"] for card in content["data"])

@pytest.mark.asyncio
async def test_get_card_by_id(client: AsyncClient) -> None:
    # Use a known Scryfall ID for Black Lotus (Alpha)
    card_id = "bd8fa327-dd41-4737-8f19-2cf5eb1f7cdd"
    response = await client.get(f"{settings.API_V1_STR}/cards/{card_id}")
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["name"] == "Black Lotus"
    assert data["id"] == card_id
