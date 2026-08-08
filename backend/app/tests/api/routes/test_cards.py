import pytest
from app.core.config import settings
from app.models.card import Card
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_local_search_finds_substring_match(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    db_session.add_all(
        [
            Card(id="ct-1", name="Command Tower", type_line="Land"),
            Card(id="lb-1", name="Lightning Bolt", type_line="Instant"),
        ]
    )
    await db_session.commit()

    response = await client.get(f'{settings.API_V1_STR}/cards/local-search?q=tower')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Command Tower"


@pytest.mark.asyncio
async def test_local_search_dedupes_reprints_by_name(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    db_session.add_all(
        [
            Card(id="ct-1", name="Command Tower", type_line="Land"),
            Card(id="ct-2", name="Command Tower", type_line="Land"),
            Card(id="ct-3", name="Command Tower", type_line="Land"),
        ]
    )
    await db_session.commit()

    response = await client.get(f'{settings.API_V1_STR}/cards/local-search?q=command')
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_local_search_empty_query_returns_empty(client: AsyncClient) -> None:
    response = await client.get(f'{settings.API_V1_STR}/cards/local-search?q=')
    assert response.status_code == 200
    assert response.json() == []


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
