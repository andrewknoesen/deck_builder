import pytest
from httpx import AsyncClient
from app.models.deck import Deck
from app.models.card import Card
from app.models.user import User
from app.main import app
from unittest.mock import AsyncMock
from app.services.scryfall import get_scryfall_service

MOCK_DECK_BOARDS = {
    "title": "Boards Test Deck", 
    "format": "Modern",
    "user_id": 101,
    "cards": [
        {"card_id": "card-main", "quantity": 1, "board": "main"},
        {"card_id": "card-side", "quantity": 1, "board": "side"},
        {"card_id": "card-maybe", "quantity": 1, "board": "maybe"},
        {"card_id": "card-default", "quantity": 1}, # Should default to main
    ]
}

@pytest.fixture
def mock_scryfall():
    mock = AsyncMock()
    mock.get_cards_by_ids.return_value = []
    return mock

@pytest.mark.asyncio
async def test_deck_boards_support(client: AsyncClient, db_session, mock_scryfall):
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall
    
    # Setup
    user = User(id=101, email="test_boards@example.com", google_sub="subboards")
    db_session.add(user)
    
    cards = [
        Card(id="card-main", name="Main Card", type_line="Creature", mana_cost="{G}"),
        Card(id="card-side", name="Side Card", type_line="Instant", mana_cost="{U}"),
        Card(id="card-maybe", name="Maybe Card", type_line="Land", mana_cost=""),
        Card(id="card-default", name="Default Card", type_line="Sorcery", mana_cost="{R}"),
    ]
    for c in cards:
        db_session.add(c)
    await db_session.commit()

    # Create Deck
    resp = await client.post("/api/v1/decks/", json=MOCK_DECK_BOARDS)
    assert resp.status_code == 200, f"Failed to create deck: {resp.text}"
    data = resp.json()
    
    # Verify boards in response
    cards_map = {c["card_id"]: c for c in data["cards"]}
    
    assert cards_map["card-main"]["board"] == "main"
    assert cards_map["card-side"]["board"] == "side"
    assert cards_map["card-maybe"]["board"] == "maybe"
    assert cards_map["card-default"]["board"] == "main" # Default check
    
    # Retrieve Deck specific endpoint
    deck_id = data["id"]
    get_resp = await client.get(f"/api/v1/decks/{deck_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    
    get_cards_map = {c["card_id"]: c for c in get_data["cards"]}
    assert get_cards_map["card-maybe"]["board"] == "maybe"
    
    app.dependency_overrides.clear()
