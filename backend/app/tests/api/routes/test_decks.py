from unittest.mock import AsyncMock

import pytest
from app.api.deps import get_current_user
from app.core.config import settings
from app.main import app
from app.models.user import User
from app.services.scryfall import get_scryfall_service
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
def mock_scryfall():
    mock = AsyncMock()
    mock.get_cards_by_ids.return_value = []
    app.dependency_overrides[get_scryfall_service] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_scryfall_service, None)


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


@pytest.mark.asyncio
async def test_cannot_access_another_users_deck(client: AsyncClient, db_session: AsyncSession) -> None:
    owner = User(email="owner@example.com", google_sub="owner_sub", full_name="Owner")
    other = User(email="other@example.com", google_sub="other_sub", full_name="Other")
    db_session.add(owner)
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    # Create a deck as the owner (get_current_user's dev stub returns the first
    # user in the db, so it resolves to `owner` here since no override is set yet)
    create_res = await client.post(
        f"{settings.API_V1_STR}/decks/", json={"title": "Private Deck", "user_id": owner.id}
    )
    deck_id = create_res.json()["id"]

    # Now act as `other`
    app.dependency_overrides[get_current_user] = lambda: other
    try:
        read_res = await client.get(f"{settings.API_V1_STR}/decks/{deck_id}")
        assert read_res.status_code == 403

        update_res = await client.put(
            f"{settings.API_V1_STR}/decks/{deck_id}", json={"title": "Hijacked"}
        )
        assert update_res.status_code == 403

        delete_res = await client.delete(f"{settings.API_V1_STR}/decks/{deck_id}")
        assert delete_res.status_code == 403

        stats_res = await client.get(f"{settings.API_V1_STR}/decks/{deck_id}/stats")
        assert stats_res.status_code == 403

        list_res = await client.get(f"{settings.API_V1_STR}/decks/")
        assert all(d["id"] != deck_id for d in list_res.json())
    finally:
        app.dependency_overrides.pop(get_current_user, None)
