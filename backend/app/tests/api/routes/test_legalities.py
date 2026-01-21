import pytest
from httpx import AsyncClient
from app.models.user import User
from app.main import app
from unittest.mock import AsyncMock
from app.services.scryfall import get_scryfall_service

MOCK_DECK_WITH_ILLEGAL = {
    "title": "Illegal Test Deck", 
    "format": "Standard",
    "user_id": 1,
    "cards": [
        {"card_id": "banned-card", "quantity": 1, "board": "main"},
        {"card_id": "legal-card", "quantity": 1, "board": "main"},
    ]
}

@pytest.fixture
def mock_scryfall_response():
    return [
        {
            "id": "banned-card",
            "name": "Banned Card",
            "mana_cost": "{1}",
            "type_line": "Artifact",
            "legalities": {
                "standard": "banned",
                "commander": "legal"
            },
            "image_uris": {"normal": "http://img"},
            "colors": [],
            "produced_mana": []
        },
        {
            "id": "legal-card",
            "name": "Legal Card",
            "mana_cost": "{1}",
            "type_line": "Creature",
            "legalities": {
                "standard": "legal",
                "commander": "legal"
            },
            "image_uris": {"normal": "http://img"},
            "colors": [],
            "produced_mana": []
        }
    ]

@pytest.fixture
def mock_scryfall(mock_scryfall_response):
    mock = AsyncMock()
    mock.get_cards_by_ids.return_value = mock_scryfall_response
    return mock

@pytest.mark.asyncio
async def test_legalities_sync(client: AsyncClient, db_session, mock_scryfall):
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall
    
    # Create User
    user = User(id=1, email="test@example.com", google_sub="sub123")
    db_session.add(user)
    await db_session.commit()
    
    # Create Deck (triggers sync_cards because cards missing from DB)
    resp = await client.post("/api/v1/decks/", json=MOCK_DECK_WITH_ILLEGAL)
    assert resp.status_code == 200
    data = resp.json()
    
    app.dependency_overrides.clear()
    
    # Check if deck returned has valid card info including legalities
    assert len(data["cards"]) == 2
    
    banned_card = next(c for c in data["cards"] if c["card_id"] == "banned-card")
    legal_card = next(c for c in data["cards"] if c["card_id"] == "legal-card")
    
    # Verify legailties were saved and returned
    assert banned_card["card"]["legalities"]["standard"] == "banned"
    assert legal_card["card"]["legalities"]["standard"] == "legal"
