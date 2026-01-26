import pytest
from httpx import AsyncClient
from app.models.deck import Deck
from app.models.card import Card
from app.models.user import User
from app.main import app

# Mock data for tests
MOCK_DECK_WITH_STATS = {
    "title": "Stats Test Deck", 
    "format": "Commander",
    "user_id": 102,
    "cards": [
        # Land (W)
        {"card_id": "plains-1", "quantity": 10, "board": "main"},
        # Creature (W) - CMC 1
        {"card_id": "creature-w-1", "quantity": 4, "board": "main"},
        # Artifact (C) - Ramp - CMC 2
        {"card_id": "sol-ring", "quantity": 1, "board": "main"},
        # Instant (U) - CMC 3
        {"card_id": "counterspell", "quantity": 4, "board": "main"},
        # Sorcery (R) - CMC 5
        {"card_id": "big-boom", "quantity": 2, "board": "main"},
        # Sideboard Card (Should be ignored)
        {"card_id": "plains-1", "quantity": 5, "board": "side"},
    ]
}

from unittest.mock import AsyncMock
from app.services.scryfall import get_scryfall_service

@pytest.fixture
def mock_scryfall():
    mock = AsyncMock()
    # Return empty list to simulate no need to fetch or empty fetch
    mock.get_cards_by_ids.return_value = []
    return mock

@pytest.mark.asyncio
async def test_get_deck_stats(client: AsyncClient, db_session, mock_scryfall):
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall
    
    # 0. Create User
    user = User(id=102, email="test_stats@example.com", google_sub="substats")
    db_session.add(user)
    
    # 1. Create Cards in DB
    cards_to_create = [
        Card(id="plains-1", name="Plains", type_line="Basic Land — Plains", produced_mana=["W"], mana_cost=""),
        Card(id="creature-w-1", name="White Weenie", type_line="Creature", mana_cost="{W}", produced_mana=[]),
        Card(id="sol-ring", name="Sol Ring", type_line="Artifact", mana_cost="{1}", oracle_text="Add {2}", produced_mana=["C"]),
        Card(id="counterspell", name="Counterspell", type_line="Instant", mana_cost="{U}{U}", produced_mana=[]),
        Card(id="big-boom", name="Big Boom", type_line="Sorcery", mana_cost="{3}{R}{R}", produced_mana=[]),
    ]
    for card in cards_to_create:
        db_session.add(card)
    await db_session.commit()

    # 2. Create Deck via API (to ensure relationships are built)
    # We cheat a bit and use the endpoint which handles logic
    resp = await client.post("/api/v1/decks/", json=MOCK_DECK_WITH_STATS)
    assert resp.status_code == 200
    deck_id = resp.json()["id"]

    # 3. Call Stats Endpoint
    stats_resp = await client.get(f"/api/v1/decks/{deck_id}/stats")
    assert stats_resp.status_code == 200
    data = stats_resp.json()

    app.dependency_overrides.clear()

    # 4. Verify Content
    assert data["total_cards"] == 21 # 10+4+1+4+2
    
    # Check Mana Curve
    # 1 CMC: 4 (White Weenie) + 1 (Sol Ring - CMC 1) = 5
    # 2 CMC: 4 (Counterspell) -> Wait, UU is CMC 2
    # 5 CMC: 2 (Big Boom)
    # Lands (0 CMC?) -> Excluded from curve usually or 0. Logic says "non_lands" in service.
    
    # Let's check the service logic expectations:
    # Sol Ring: {1} -> CMC 1
    # Creature: {W} -> CMC 1
    # Counterspell: {U}{U} -> CMC 2
    # Big Boom: {3}{R}{R} -> CMC 5
    
    curve = data["mana_curve"]
    assert curve["1"] == 5 # 4 creatures + 1 sol ring
    assert curve["2"] == 4 # 4 counterspells
    assert curve["5"] == 2 # 2 big booms
    assert curve["0"] == 0
    
    # Check Colors
    colors = data["color_stats"]
    assert colors["W"]["pips"] == 4 # 4 * {W}
    # Sol Ring produced C, Plains produced W.
    # We have 10 Plains -> 10 W sources
    assert colors["W"]["sources"] == 10
    
    # Check Recommendations
    recs = data["recommendations"]
    assert recs["ramp_count"] == 1 # Sol Ring
    
    # Check Draw Odds
    odds = data["draw_odds"]
    assert "opening_hand" in odds
    assert "on_curve" in odds
