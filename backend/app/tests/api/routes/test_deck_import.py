from unittest.mock import AsyncMock

import httpx
import pytest
from app.main import app
from app.models.user import User
from app.services.scryfall import get_scryfall_service
from httpx import AsyncClient

SIMPLE_LIST = """About
Name Dredge

Deck
4 Blanchwood Prowler
2 Gnaw to the Bone

Sideboard
2 Gnaw to the Bone
"""


def _card(card_id: str, name: str, **overrides) -> dict:
    return {
        "id": card_id,
        "name": name,
        "mana_cost": "{1}",
        "type_line": "Creature",
        "oracle_text": "",
        "colors": [],
        "produced_mana": [],
        "image_uris": {"normal": "http://img"},
        "legalities": {"commander": "legal"},
        **overrides,
    }


def _collection_mock(known_by_name: dict) -> AsyncMock:
    """
    Fakes ScryfallService.get_collection against a name -> card map, matching
    the real /cards/collection response shape: {"data": [...], "not_found": [...]}.
    """
    mock = AsyncMock()

    async def fake_get_collection(identifiers):
        data, not_found = [], []
        for ident in identifiers:
            card = known_by_name.get(ident.get("name", "").lower())
            (data if card else not_found).append(card or ident)
        return {"data": data, "not_found": not_found}

    mock.get_collection.side_effect = fake_get_collection
    mock.get_cards_by_ids.side_effect = lambda ids: [_card(cid, cid) for cid in ids]
    return mock


@pytest.fixture
def mock_scryfall():
    return _collection_mock(
        {
            "blanchwood prowler": _card("prowler-1", "Blanchwood Prowler"),
            "gnaw to the bone": _card("gnaw-1", "Gnaw to the Bone"),
        }
    )


async def _create_user(db_session, user_id=1) -> User:
    user = User(id=user_id, email=f"user{user_id}@example.com", google_sub=f"sub{user_id}")
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_import_deck_success(client: AsyncClient, db_session, mock_scryfall):
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall
    await _create_user(db_session)

    resp = await client.post("/api/v1/decks/import", json={"text": SIMPLE_LIST})
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Dredge"  # picked up from the "Name" header
    assert data["missing_cards"] == []


@pytest.mark.asyncio
async def test_import_deck_batches_resolution_into_one_scryfall_request(
    client: AsyncClient, db_session
):
    """
    Regression test: importing used to issue one Scryfall search per line
    (21 sequential requests for a real 21-line decklist), which was enough
    to trip Scryfall's rate limit and 500 the whole import. Resolution must
    go through a single batched /cards/collection call instead.
    """
    names = [f"Real Card {i}" for i in range(20)]
    mock_scryfall = _collection_mock(
        {name.lower(): _card(f"card-{i}", name) for i, name in enumerate(names)}
    )
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall
    await _create_user(db_session)

    text = "\n".join(f"1 {name}" for name in names)
    resp = await client.post("/api/v1/decks/import", json={"text": text})
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["missing_cards"] == []
    assert mock_scryfall.get_collection.call_count == 1
    assert mock_scryfall.search_cards.call_count == 0


@pytest.mark.asyncio
async def test_import_deck_respects_name_override(
    client: AsyncClient, db_session, mock_scryfall
):
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall
    await _create_user(db_session)

    resp = await client.post(
        "/api/v1/decks/import", json={"text": SIMPLE_LIST, "name": "My Custom Name"}
    )
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["title"] == "My Custom Name"


@pytest.mark.asyncio
async def test_import_deck_merges_duplicate_lines_same_board(
    client: AsyncClient, db_session, mock_scryfall
):
    """
    'Gnaw to the Bone' appears once in Deck (main) and once in Sideboard
    (side) in SIMPLE_LIST - different boards, so both rows persist without
    violating DeckCard's (deck_id, card_id, board) primary key.
    """
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall
    await _create_user(db_session)

    resp = await client.post("/api/v1/decks/import", json={"text": SIMPLE_LIST})
    deck_id = resp.json()["id"]

    deck_resp = await client.get(f"/api/v1/decks/{deck_id}")
    app.dependency_overrides.clear()

    cards = deck_resp.json()["cards"]
    gnaw_cards = [c for c in cards if c["card_id"] == "gnaw-1"]
    assert len(gnaw_cards) == 2
    assert {c["board"] for c in gnaw_cards} == {"main", "side"}


@pytest.mark.asyncio
async def test_import_deck_partial_failure_reports_missing_cards(
    client: AsyncClient, db_session
):
    mock = _collection_mock({"real card": _card("real-1", "Real Card")})
    app.dependency_overrides[get_scryfall_service] = lambda: mock
    await _create_user(db_session)

    text = "2 Real Card\n3 Totally Fake Card That Does Not Exist"
    resp = await client.post("/api/v1/decks/import", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()

    deck_resp = await client.get(f"/api/v1/decks/{data['id']}")
    app.dependency_overrides.clear()

    assert data["missing_cards"] == ["3 Totally Fake Card That Does Not Exist"]
    cards = deck_resp.json()["cards"]
    assert len(cards) == 1
    assert cards[0]["card_id"] == "real-1"


@pytest.mark.asyncio
async def test_import_deck_resolves_adventure_card_by_front_face(
    client: AsyncClient, db_session
):
    """
    Regression test: Scryfall's /cards/collection always returns adventure/
    split/MDFC cards under their combined "Front // Back" name, even when
    queried by the front face alone (the way decklists spell them, e.g.
    "Sagu Wildling" for "Sagu Wildling // Roost Seek"). Resolution must fall
    back to matching on the front face or these cards get reported missing.
    """
    mock = _collection_mock(
        {"sagu wildling": _card("sagu-1", "Sagu Wildling // Roost Seek")}
    )
    app.dependency_overrides[get_scryfall_service] = lambda: mock
    await _create_user(db_session)

    resp = await client.post("/api/v1/decks/import", json={"text": "2 Sagu Wildling"})
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["missing_cards"] == []


@pytest.mark.asyncio
async def test_import_deck_scryfall_error_still_reports_missing_not_500(
    client: AsyncClient, db_session
):
    """
    If the collection lookup itself errors (e.g. a transient 429/500), the
    whole import must not crash - everything in that chunk is reported as
    missing instead.
    """
    mock = AsyncMock()
    mock.get_collection.side_effect = httpx.HTTPStatusError(
        "Too Many Requests",
        request=httpx.Request("GET", "http://test"),
        response=httpx.Response(429, request=httpx.Request("GET", "http://test")),
    )
    app.dependency_overrides[get_scryfall_service] = lambda: mock
    await _create_user(db_session)

    resp = await client.post("/api/v1/decks/import", json={"text": "2 Real Card"})
    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["missing_cards"] == ["2 Real Card"]


@pytest.mark.asyncio
async def test_import_deck_belongs_to_requesting_user(
    client: AsyncClient, db_session, mock_scryfall
):
    app.dependency_overrides[get_scryfall_service] = lambda: mock_scryfall
    await _create_user(db_session, user_id=7)

    resp = await client.post("/api/v1/decks/import", json={"text": SIMPLE_LIST})
    deck_id = resp.json()["id"]
    app.dependency_overrides.clear()

    from sqlmodel import select
    from app.models.deck import Deck

    result = await db_session.execute(select(Deck).where(Deck.id == deck_id))
    assert result.scalar_one().user_id == 7
