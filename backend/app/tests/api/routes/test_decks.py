import pytest
from app.core.config import settings
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_deck_with_cards(client: AsyncClient, db_session: AsyncSession) -> None:
    # First create a user because deck has a foreign key to user
    user = User(email="test_cards@example.com", google_sub="abc123_cards", full_name="Test User Cards")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    deck_data = {
        "title": "Test Deck with Cards", 
        "format": "Standard", 
        "user_id": user.id,
        "cards": [
            {"card_id": "card-1", "quantity": 4, "board": "main"},
            {"card_id": "card-2", "quantity": 1, "board": "side"}
        ]
    }
    response = await client.post(f"{settings.API_V1_STR}/decks/", json=deck_data)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["title"] == "Test Deck with Cards"
    assert len(data["cards"]) == 2
    assert data["cards"][0]["card_id"] == "card-1"
    assert data["cards"][1]["quantity"] == 1

@pytest.mark.asyncio
async def test_update_deck_cards(client: AsyncClient, db_session: AsyncSession) -> None:
    user = User(email="test_update@example.com", google_sub="upd123", full_name="Update User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 1. Create deck
    create_res = await client.post(f"{settings.API_V1_STR}/decks/", json={
        "title": "Initial Deck", "user_id": user.id, "cards": [{"card_id": "old-card", "quantity": 1, "board": "main"}]
    })
    deck_id = create_res.json()["id"]

    # 2. Update deck (replace cards)
    update_data = {
        "title": "Updated Deck",
        "cards": [{"card_id": "new-card", "quantity": 4, "board": "main"}]
    }
    response = await client.put(f"{settings.API_V1_STR}/decks/{deck_id}", json=update_data)
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["title"] == "Updated Deck"
    assert len(data["cards"]) == 1
    assert data["cards"][0]["card_id"] == "new-card"

@pytest.mark.asyncio
async def test_read_decks(client: AsyncClient, db_session: AsyncSession) -> None:
    # Ensure at least one deck exists
    user = User(email="test2@example.com", google_sub="def456", full_name="Test User 2")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    deck_data = {"title": "My Decks", "user_id": user.id}
    await client.post(f"{settings.API_V1_STR}/decks/", json=deck_data)

    response = await client.get(f"{settings.API_V1_STR}/decks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(d["title"] == "My Decks" for d in data)


@pytest.mark.asyncio
async def test_get_deck_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    user = User(email="test3@example.com", google_sub="ghi789", full_name="Test User 3")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    deck_data = {"title": "Solo Deck", "user_id": user.id}
    create_res = await client.post(f"{settings.API_V1_STR}/decks/", json=deck_data)
    deck_id = create_res.json()["id"]

    response = await client.get(f"{settings.API_V1_STR}/decks/{deck_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Solo Deck"
    assert data["id"] == deck_id
