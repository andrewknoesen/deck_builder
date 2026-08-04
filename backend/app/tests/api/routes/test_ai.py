from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from app.core.config import settings
from app.main import app
from app.models.user import User
from app.services.scryfall import get_scryfall_service
from google.adk.runners import InMemoryRunner
from httpx import AsyncClient

MOCK_DECK = {
    "title": "Advisor Test Deck",
    "format": "Commander",
    "user_id": 201,
    "cards": [
        {"card_id": "sol-ring", "quantity": 1, "board": "main"},
        {"card_id": "plains-1", "quantity": 10, "board": "main"},
    ],
}


@pytest.fixture
def mock_scryfall():
    mock = AsyncMock()
    mock.get_cards_by_ids.return_value = [
        {
            "id": "sol-ring",
            "name": "Sol Ring",
            "mana_cost": "{1}",
            "type_line": "Artifact",
            "oracle_text": "Add {2}",
            "colors": [],
            "produced_mana": ["C"],
            "legalities": {"commander": "legal"},
        },
        {
            "id": "plains-1",
            "name": "Plains",
            "mana_cost": "",
            "type_line": "Basic Land — Plains",
            "colors": [],
            "produced_mana": ["W"],
            "legalities": {"commander": "legal"},
        },
    ]
    return mock


def _fake_run_async_returning(text: str):
    async def fake_run_async(self, *, user_id, session_id, new_message, **kwargs):
        event = SimpleNamespace(
            content=SimpleNamespace(parts=[SimpleNamespace(text=text)]),
            is_final_response=lambda: True,
        )
        yield event

    return fake_run_async


@pytest.mark.asyncio
async def test_ai_suggest(client: AsyncClient, db_session, mock_scryfall) -> None:
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall

    user = User(id=201, email="advisor@example.com", google_sub="advisor_sub")
    db_session.add(user)
    await db_session.commit()

    create_res = await client.post(f"{settings.API_V1_STR}/decks/", json=MOCK_DECK)
    assert create_res.status_code == 200
    deck_id = create_res.json()["id"]

    fake_run_async = _fake_run_async_returning(
        "**Suggestions**: Add Arcane Signet (real card from search_cards) — ramp.\n"
        "**Summary**: Curve is fine, add more ramp."
    )

    captured_message = {}

    async def capturing_run_async(self, *, user_id, session_id, new_message, **kwargs):
        captured_message["text"] = new_message.parts[0].text
        async for event in fake_run_async(
            self, user_id=user_id, session_id=session_id, new_message=new_message
        ):
            yield event

    with patch.object(InMemoryRunner, "run_async", capturing_run_async):
        response = await client.post(
            f"{settings.API_V1_STR}/ai/suggest",
            json={"deck_id": deck_id, "query": "What should I add?"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "Arcane Signet" in response.json()["response"]

    # The context handed to the agent should carry the deck's own cards/stats,
    # not just the raw query — this is what makes suggestions deck-aware.
    context = captured_message["text"]
    assert "Sol Ring" in context
    assert "Plains" in context
    assert "Commander" in context
    assert "What should I add?" in context

    # Each existing card's own mana cost/type/legality is in the context so the
    # agent doesn't need a search_cards round trip just to re-look-up a card it
    # was already told about.
    assert "Commander legality: legal" in context


@pytest.mark.asyncio
async def test_ai_suggest_respects_format_legality_context(
    client: AsyncClient, db_session, mock_scryfall
) -> None:
    """The deck's format is threaded into the agent context so it can filter
    suggestions by legality (the agent itself is mocked here; enforcement of
    legality is the agent's job via search_cards, exercised in test_cards_tool)."""
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall

    user = User(id=202, email="advisor2@example.com", google_sub="advisor_sub2")
    db_session.add(user)
    await db_session.commit()

    standard_deck = {**MOCK_DECK, "user_id": 202, "format": "Standard"}
    create_res = await client.post(f"{settings.API_V1_STR}/decks/", json=standard_deck)
    deck_id = create_res.json()["id"]

    captured_message = {}

    async def capturing_run_async(self, *, user_id, session_id, new_message, **kwargs):
        captured_message["text"] = new_message.parts[0].text
        event = SimpleNamespace(
            content=SimpleNamespace(parts=[SimpleNamespace(text="ok")]),
            is_final_response=lambda: True,
        )
        yield event

    with patch.object(InMemoryRunner, "run_async", capturing_run_async):
        response = await client.post(
            f"{settings.API_V1_STR}/ai/suggest",
            json={"deck_id": deck_id, "query": "anything cheap?"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert "Format: Standard" in captured_message["text"]


@pytest.mark.asyncio
async def test_ai_suggest_rejects_deck_owned_by_another_user(
    client: AsyncClient, db_session, mock_scryfall
) -> None:
    from app.api.deps import get_current_user

    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall

    owner = User(email="owner_ai@example.com", google_sub="owner_ai_sub")
    other = User(email="other_ai@example.com", google_sub="other_ai_sub")
    db_session.add(owner)
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(owner)
    await db_session.refresh(other)

    create_res = await client.post(
        f"{settings.API_V1_STR}/decks/",
        json={"title": "Private Deck", "user_id": owner.id, "cards": []},
    )
    deck_id = create_res.json()["id"]

    app.dependency_overrides[get_current_user] = lambda: other
    try:
        response = await client.post(
            f"{settings.API_V1_STR}/ai/suggest",
            json={"deck_id": deck_id, "query": "anything?"},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ai_suggest_deck_not_found(client: AsyncClient, db_session) -> None:
    response = await client.post(
        f"{settings.API_V1_STR}/ai/suggest",
        json={"deck_id": 999999, "query": "anything?"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ai_chat(client: AsyncClient) -> None:
    async def fake_run_async(self, *, user_id, session_id, new_message, **kwargs):
        event = SimpleNamespace(
            content=SimpleNamespace(parts=[SimpleNamespace(text="[CR 702.1] Flying rules.")]),
            is_final_response=lambda: True,
        )
        yield event

    with patch.object(InMemoryRunner, "run_async", fake_run_async):
        response = await client.post(
            f"{settings.API_V1_STR}/ai/chat", json={"message": "What is flying?"}
        )

    assert response.status_code == 200
    assert response.json() == {"response": "[CR 702.1] Flying rules."}
