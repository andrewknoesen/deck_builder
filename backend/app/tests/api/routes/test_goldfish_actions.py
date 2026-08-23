from unittest.mock import AsyncMock

import pytest
from app.api.deps import get_current_user
from app.core.config import settings
from app.main import app
from app.models.card import Card
from app.models.goldfish import GameState, GoldfishNode, GoldfishSession
from app.models.user import User
from app.services.scryfall import get_scryfall_service
from httpx import AsyncClient


async def _make_deck_with_cards(
    client: AsyncClient,
    db_session,
    email: str,
    sub: str,
    deck_format: str | None = None,
):
    """
    A deck with two distinct mainboard cards (3x CardA, 1x CardB) plus a
    sideboard card that should never show up in the virtual library.
    """
    user = User(email=email, google_sub=sub, full_name="Test User")
    db_session.add(user)

    cards = [
        Card(id="card-a", name="Card A", type_line="Creature", produced_mana=[]),
        Card(id="card-b", name="Card B", type_line="Instant", produced_mana=[]),
        Card(id="card-side", name="Card Side", type_line="Sorcery", produced_mana=[]),
    ]
    for card in cards:
        db_session.add(card)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides[get_scryfall_service] = lambda: AsyncMock()
    try:
        deck_res = await client.post(
            f"{settings.API_V1_STR}/decks/",
            json={
                "title": "Simulator Deck",
                "format": deck_format,
                "user_id": user.id,
                "cards": [
                    {"card_id": "card-a", "quantity": 3, "board": "main"},
                    {"card_id": "card-b", "quantity": 1, "board": "main"},
                    {"card_id": "card-side", "quantity": 1, "board": "side"},
                ],
            },
        )
    finally:
        del app.dependency_overrides[get_scryfall_service]
    assert deck_res.status_code == 200
    return user, deck_res.json()["id"]


async def _make_deck_for_user(
    client: AsyncClient,
    db_session,
    user: User,
    title: str,
    cards: list[dict],
    deck_format: str | None = None,
):
    """
    Creates a deck for an *existing* user — unlike `_make_deck_with_cards`/
    `_make_deck_with_many_cards`, which each create a brand-new `User` with a
    unique email/google_sub. Needed to get "two decks, one owner" (or "two
    decks, different owners" by passing two different `User`s) for Phase 3d's
    two-deck goldfishing tests, which the unique email/sub constraint on
    `User` otherwise makes impossible via the existing helpers.
    """
    app.dependency_overrides[get_scryfall_service] = lambda: AsyncMock()
    try:
        deck_res = await client.post(
            f"{settings.API_V1_STR}/decks/",
            json={
                "title": title,
                "format": deck_format,
                "user_id": user.id,
                "cards": cards,
            },
        )
    finally:
        del app.dependency_overrides[get_scryfall_service]
    assert deck_res.status_code == 200
    return deck_res.json()["id"]


async def _make_deck_with_many_cards(
    client: AsyncClient, db_session, email: str, sub: str
):
    """
    10 copies of a single mainboard card — enough to test a real 7-card
    opening hand draw distinctly from "drew everything because the library
    was too small to fill a hand."
    """
    user = User(email=email, google_sub=sub, full_name="Test User")
    db_session.add(user)
    db_session.add(
        Card(id="card-many", name="Many Card", type_line="Land", produced_mana=["C"])
    )
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides[get_scryfall_service] = lambda: AsyncMock()
    try:
        deck_res = await client.post(
            f"{settings.API_V1_STR}/decks/",
            json={
                "title": "Big Deck",
                "user_id": user.id,
                "cards": [{"card_id": "card-many", "quantity": 10, "board": "main"}],
            },
        )
    finally:
        del app.dependency_overrides[get_scryfall_service]
    assert deck_res.status_code == 200
    return user, deck_res.json()["id"]


async def _get_root(client: AsyncClient, session_id: int):
    """
    The true "Game start" root (parent_id None) — not just nodes[0], since a
    session with any mainboard cards now also auto-creates an opening-hand
    child node right after it.
    """
    tree = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    ).json()
    return next(n for n in tree["nodes"] if n["parent_id"] is None)


async def _make_deck_with_mana_cards(
    client: AsyncClient, db_session, email: str, sub: str
):
    """
    A deck with one copy each of five distinctly-costed nonland cards
    (generic, colored, hybrid, Phyrexian, {X}) plus a land — enough to move
    any specific one from library to hand deterministically (via `move_zone`,
    which doesn't care about library order) and cast it.
    """
    user = User(email=email, google_sub=sub, full_name="Test User")
    db_session.add(user)

    cards = [
        Card(
            id="mana-land",
            name="Mana Land",
            type_line="Land",
            mana_cost="",
            produced_mana=["C"],
        ),
        Card(
            id="mana-generic",
            name="Generic Card",
            type_line="Artifact",
            mana_cost="{2}",
            produced_mana=[],
        ),
        Card(
            id="mana-color",
            name="Colored Card",
            type_line="Instant",
            mana_cost="{R}",
            produced_mana=[],
        ),
        Card(
            id="mana-hybrid",
            name="Hybrid Card",
            type_line="Sorcery",
            mana_cost="{G/U}",
            produced_mana=[],
        ),
        Card(
            id="mana-phyrexian",
            name="Phyrexian Card",
            type_line="Creature",
            mana_cost="{G/P}",
            produced_mana=[],
        ),
        Card(
            id="mana-x",
            name="X Card",
            type_line="Sorcery",
            mana_cost="{X}{R}",
            produced_mana=[],
        ),
    ]
    for card in cards:
        db_session.add(card)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides[get_scryfall_service] = lambda: AsyncMock()
    try:
        deck_res = await client.post(
            f"{settings.API_V1_STR}/decks/",
            json={
                "title": "Mana Test Deck",
                "user_id": user.id,
                "cards": [
                    {"card_id": c.id, "quantity": 1, "board": "main"} for c in cards
                ],
            },
        )
    finally:
        del app.dependency_overrides[get_scryfall_service]
    assert deck_res.status_code == 200
    return user, deck_res.json()["id"]


async def _move_to_hand(
    client: AsyncClient,
    session_id: int,
    parent_id: int,
    card_id: str,
    target: str = "self",
):
    res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": parent_id,
            "action": {
                "type": "move_zone",
                "card_id": card_id,
                "from_zone": "library",
                "to_zone": "hand",
                "target": target,
            },
        },
    )
    assert res.status_code == 200
    return res.json()


async def _cast(
    client: AsyncClient,
    session_id: int,
    parent_id: int,
    card_id: str,
    target: str = "self",
):
    res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": parent_id,
            "action": {"type": "cast", "card_id": card_id, "target": target},
        },
    )
    assert res.status_code == 200
    return res.json()


async def _make_two_deck_session(
    client: AsyncClient,
    db_session,
    email: str,
    sub: str,
    primary_cards: list[dict],
    opponent_cards: list[dict],
):
    """
    One user, a primary deck and an opponent deck (Card rows must already be
    committed by the caller), and a freshly created 2-deck goldfish session.
    Returns (user, session_id, tree) where `tree` is the session's full node
    list right after creation (root + the combined opening-hand node).
    """
    user = User(email=email, google_sub=sub)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    deck_id = await _make_deck_for_user(
        client, db_session, user, "Primary Deck", primary_cards
    )
    opponent_deck_id = await _make_deck_for_user(
        client, db_session, user, "Opponent Deck", opponent_cards
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions",
            json={"deck_id": deck_id, "opponent_deck_id": opponent_deck_id},
        )
    ).json()["id"]
    tree = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    ).json()
    return user, session_id, tree


@pytest.mark.asyncio
async def test_session_auto_shuffles_mainboard_only(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim1@example.com", "sim_sub_1", "Commander"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    root = await _get_root(client, session_id)
    library = root["state"]["library"]

    assert len(library) == 4  # 3x card-a + 1x card-b, sideboard excluded
    assert sorted(library) == sorted(["card-a", "card-a", "card-a", "card-b"])
    assert root["state"]["life_total"] == 40  # Commander


@pytest.mark.asyncio
async def test_draw_action_moves_top_card_to_hand(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim2@example.com", "sim_sub_2"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)
    library_before = list(root["state"]["library"])

    draw_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": root["id"], "action": {"type": "draw"}},
    )
    assert draw_res.status_code == 200
    node = draw_res.json()

    assert len(node["state"]["hand"]) == 1
    assert node["state"]["hand"][0] == library_before[0]
    assert len(node["state"]["library"]) == len(library_before) - 1
    assert (
        node["label"]
        == f"Drew {'Card A' if library_before[0] == 'card-a' else 'Card B'}"
    )


@pytest.mark.asyncio
async def test_draw_with_empty_library_does_not_crash(
    client: AsyncClient, db_session
) -> None:
    user = User(email="sim3@example.com", google_sub="sim_sub_3")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    deck_res = await client.post(
        f"{settings.API_V1_STR}/decks/",
        json={"title": "Empty Deck", "user_id": user.id, "cards": []},
    )
    deck_id = deck_res.json()["id"]

    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    draw_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": root["id"], "action": {"type": "draw"}},
    )
    assert draw_res.status_code == 200
    node = draw_res.json()
    assert node["state"]["hand"] == []
    assert "empty library" in node["label"].lower()


@pytest.mark.asyncio
async def test_play_land_and_cast_move_hand_to_battlefield(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim4@example.com", "sim_sub_4"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    draw = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
            json={"parent_id": root["id"], "action": {"type": "draw"}},
        )
    ).json()
    drawn_card_id = draw["state"]["hand"][0]

    cast_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": draw["id"],
            "action": {"type": "cast", "card_id": drawn_card_id},
        },
    )
    assert cast_res.status_code == 200
    node = cast_res.json()
    assert node["state"]["hand"] == []
    assert node["state"]["battlefield"] == [drawn_card_id]
    assert node["label"].startswith("Cast ")


@pytest.mark.asyncio
async def test_cast_card_not_in_hand_400(client: AsyncClient, db_session) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim5@example.com", "sim_sub_5"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": root["id"],
            "action": {"type": "cast", "card_id": "card-a"},
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_move_zone_arbitrary_and_invalid_source(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim6@example.com", "sim_sub_6"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    draw = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
            json={"parent_id": root["id"], "action": {"type": "draw"}},
        )
    ).json()
    drawn_card_id = draw["state"]["hand"][0]

    move_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": draw["id"],
            "action": {
                "type": "move_zone",
                "card_id": drawn_card_id,
                "from_zone": "hand",
                "to_zone": "graveyard",
            },
        },
    )
    assert move_res.status_code == 200
    node = move_res.json()
    assert node["state"]["hand"] == []
    assert node["state"]["graveyard"] == [drawn_card_id]

    # Card is no longer in hand - moving it "from hand" again is a data
    # integrity error, not a legality question, so this is a 400.
    invalid_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": node["id"],
            "action": {
                "type": "move_zone",
                "card_id": drawn_card_id,
                "from_zone": "hand",
                "to_zone": "exile",
            },
        },
    )
    assert invalid_res.status_code == 400


@pytest.mark.asyncio
async def test_set_life_action(client: AsyncClient, db_session) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim7@example.com", "sim_sub_7"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)
    assert root["state"]["life_total"] == 20

    life_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": root["id"],
            "action": {"type": "set_life", "life_total": 17},
        },
    )
    assert life_res.status_code == 200
    node = life_res.json()
    assert node["state"]["life_total"] == 17
    assert node["label"] == "Life: 20 → 17"


@pytest.mark.asyncio
async def test_set_life_action_supports_opponent_target(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim_opp@example.com", "sim_sub_opp"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)
    assert root["state"]["life_total"] == 20
    assert root["state"]["opponent_life_total"] == 20

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": root["id"],
            "action": {"type": "set_life", "life_total": 17, "target": "opponent"},
        },
    )
    assert response.status_code == 200
    node = response.json()
    assert node["state"]["opponent_life_total"] == 17
    assert node["state"]["life_total"] == 20  # unaffected
    assert node["label"] == "Opponent life: 20 → 17"


@pytest.mark.asyncio
async def test_session_auto_draws_opening_hand_of_seven(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_many_cards(
        client, db_session, "sim_open1@example.com", "sim_sub_open1"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    tree = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    ).json()
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])

    # The root itself is the pure pre-game snapshot, untouched.
    assert root["state"]["hand"] == []
    assert len(root["state"]["library"]) == 10

    assert len(opening["state"]["hand"]) == 7
    assert len(opening["state"]["library"]) == 3
    assert opening["label"] == "Drew opening hand (7 cards)"


@pytest.mark.asyncio
async def test_session_opening_hand_draws_fewer_when_library_small(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim_open2@example.com", "sim_sub_open2"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    tree = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    ).json()
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])

    assert len(opening["state"]["hand"]) == 4  # the whole 4-card library
    assert opening["state"]["library"] == []
    assert opening["label"] == "Drew opening hand (4 cards)"


@pytest.mark.asyncio
async def test_action_requires_parent_with_state(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim8@example.com", "sim_sub_8"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    # A root-level (parent_id omitted) node has no parent to inherit state
    # from, and actions have nothing to apply against.
    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"action": {"type": "draw"}},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_freeform_note_carries_state_forward_unchanged(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim9@example.com", "sim_sub_9"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    note_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": root["id"], "label": "Opponent passed the turn"},
    )
    assert note_res.status_code == 200
    node = note_res.json()
    assert node["state"] == root["state"]


@pytest.mark.asyncio
async def test_shuffle_action_reorders_library_without_changing_contents(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_many_cards(
        client, db_session, "sim_shuffle@example.com", "sim_sub_shuffle"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)
    library_before = root["state"]["library"]

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": root["id"], "action": {"type": "shuffle"}},
    )
    assert response.status_code == 200
    node = response.json()

    assert node["label"] == "Shuffled library"
    assert sorted(node["state"]["library"]) == sorted(library_before)
    assert len(node["state"]["library"]) == len(library_before)
    # Every other zone is untouched by a shuffle.
    assert node["state"]["hand"] == root["state"]["hand"]
    assert node["state"]["battlefield"] == root["state"]["battlefield"]


@pytest.mark.asyncio
async def test_next_turn_action_advances_turn_number_and_auto_draws(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_many_cards(
        client, db_session, "sim_turn@example.com", "sim_sub_turn"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)
    assert root["turn_number"] is None
    library_before = root["state"]["library"]

    turn1_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": root["id"], "action": {"type": "next_turn"}},
    )
    assert turn1_res.status_code == 200
    turn1 = turn1_res.json()
    assert turn1["turn_number"] == 1
    assert turn1["label"] == "Turn 1: drew Many Card"
    # next_turn also draws a card for the turn, same as clicking Draw.
    assert turn1["state"]["hand"] == [library_before[0]]
    assert len(turn1["state"]["library"]) == len(library_before) - 1

    turn2_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": turn1["id"], "action": {"type": "next_turn"}},
    )
    turn2 = turn2_res.json()
    assert turn2["turn_number"] == 2
    assert turn2["label"] == "Turn 2: drew Many Card"
    assert len(turn2["state"]["hand"]) == 2


@pytest.mark.asyncio
async def test_next_turn_empty_library_does_not_crash(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim_turn_empty@example.com", "sim_sub_turn_empty"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    # This test deck's whole 4-card library was already drawn into the
    # opening hand (a child of root), so the library is empty from there on.
    tree = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    ).json()
    opening_hand = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    assert opening_hand["state"]["library"] == []

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": opening_hand["id"], "action": {"type": "next_turn"}},
    )
    assert response.status_code == 200
    node = response.json()
    assert node["turn_number"] == 1
    assert node["label"] == "Turn 1 (empty library)"


@pytest.mark.asyncio
async def test_next_turn_respects_explicit_label_override(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "sim_turn2@example.com", "sim_sub_turn2"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": root["id"],
            "label": "Turn 1 (on the draw)",
            "action": {"type": "next_turn"},
        },
    )
    node = response.json()
    assert node["turn_number"] == 1
    assert node["label"] == "Turn 1 (on the draw)"


# --- Phase 3d: two-deck goldfishing ---------------------------------------


@pytest.mark.asyncio
async def test_create_two_deck_session_rejects_opponent_deck_owned_by_other_user(
    client: AsyncClient, db_session
) -> None:
    # _make_deck_with_cards always seeds the same fixed card ids, so it can't
    # be called twice in one test (duplicate Card rows) — the owner's deck
    # uses it, the other user's deck uses `_make_deck_for_user` with its own
    # card instead. `POST /decks/` always assigns the *current* dev-mode user
    # as owner (`create_deck` ignores any `user_id` in the request body), so
    # `other`'s deck has to be created under a `get_current_user` override —
    # same pattern `test_goldfish.py`'s existing ownership test already uses
    # — otherwise it would silently end up owned by `owner` too.
    owner, deck_id = await _make_deck_with_cards(
        client, db_session, "twodeck_owner@example.com", "twodeck_owner_sub"
    )
    other = User(email="twodeck_other@example.com", google_sub="twodeck_other_sub")
    db_session.add(other)
    db_session.add(
        Card(id="card-other", name="Other Card", type_line="Land", produced_mana=["C"])
    )
    await db_session.commit()
    await db_session.refresh(other)

    app.dependency_overrides[get_current_user] = lambda: other
    try:
        opponent_deck_id = await _make_deck_for_user(
            client,
            db_session,
            other,
            "Other Deck",
            [{"card_id": "card-other", "quantity": 1, "board": "main"}],
        )
    finally:
        del app.dependency_overrides[get_current_user]
    assert owner.id != other.id  # sanity: current_user (dev-mode) defaults to owner

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions",
        json={"deck_id": deck_id, "opponent_deck_id": opponent_deck_id},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_two_deck_session_rejects_format_mismatch(
    client: AsyncClient, db_session
) -> None:
    user = User(email="fmt_mismatch@example.com", google_sub="fmt_mismatch_sub")
    db_session.add(user)
    db_session.add(
        Card(id="card-fmt1", name="Fmt Card 1", type_line="Creature", produced_mana=[])
    )
    db_session.add(
        Card(id="card-fmt2", name="Fmt Card 2", type_line="Creature", produced_mana=[])
    )
    await db_session.commit()
    await db_session.refresh(user)

    deck_id = await _make_deck_for_user(
        client,
        db_session,
        user,
        "Standard Deck",
        [{"card_id": "card-fmt1", "quantity": 1, "board": "main"}],
        deck_format="Standard",
    )
    opponent_deck_id = await _make_deck_for_user(
        client,
        db_session,
        user,
        "Commander Deck",
        [{"card_id": "card-fmt2", "quantity": 1, "board": "main"}],
        deck_format="Commander",
    )

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions",
        json={"deck_id": deck_id, "opponent_deck_id": opponent_deck_id},
    )
    assert response.status_code == 400

    list_res = await client.get(
        f"{settings.API_V1_STR}/goldfish/sessions", params={"deck_id": deck_id}
    )
    assert list_res.json() == []


@pytest.mark.asyncio
async def test_create_two_deck_session_allows_both_formats_none(
    client: AsyncClient, db_session
) -> None:
    user = User(email="fmt_none@example.com", google_sub="fmt_none_sub")
    db_session.add(user)
    db_session.add(
        Card(
            id="card-none1", name="None Card 1", type_line="Creature", produced_mana=[]
        )
    )
    db_session.add(
        Card(
            id="card-none2", name="None Card 2", type_line="Creature", produced_mana=[]
        )
    )
    await db_session.commit()
    await db_session.refresh(user)

    deck_id = await _make_deck_for_user(
        client,
        db_session,
        user,
        "Deck One",
        [{"card_id": "card-none1", "quantity": 1, "board": "main"}],
    )
    opponent_deck_id = await _make_deck_for_user(
        client,
        db_session,
        user,
        "Deck Two",
        [{"card_id": "card-none2", "quantity": 1, "board": "main"}],
    )

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions",
        json={"deck_id": deck_id, "opponent_deck_id": opponent_deck_id},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_two_deck_session_deals_opening_hands_of_seven_each(
    client: AsyncClient, db_session
) -> None:
    db_session.add(
        Card(id="card-p", name="Primary Card", type_line="Land", produced_mana=["C"])
    )
    db_session.add(
        Card(id="card-o", name="Opponent Card", type_line="Land", produced_mana=["C"])
    )
    await db_session.commit()

    _user, _session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "two_deck_hands@example.com",
        "two_deck_hands_sub",
        [{"card_id": "card-p", "quantity": 10, "board": "main"}],
        [{"card_id": "card-o", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])

    assert len(opening["state"]["hand"]) == 7
    assert len(opening["state"]["opponent_zones"]["hand"]) == 7
    # Composition, not just count — catches a self/opponent deck mix-up.
    assert sorted(root["state"]["opponent_zones"]["library"]) == sorted(["card-o"] * 10)
    assert opening["label"] == "Drew opening hands (7 cards each)"


@pytest.mark.asyncio
async def test_two_deck_mirror_match_self_target_never_touches_opponent_zones(
    client: AsyncClient, db_session
) -> None:
    user = User(email="mirror@example.com", google_sub="mirror_sub")
    db_session.add(user)
    db_session.add(
        Card(
            id="card-mirror", name="Mirror Card", type_line="Land", produced_mana=["C"]
        )
    )
    await db_session.commit()
    await db_session.refresh(user)

    deck_id = await _make_deck_for_user(
        client,
        db_session,
        user,
        "Mirror Deck",
        [{"card_id": "card-mirror", "quantity": 10, "board": "main"}],
    )

    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions",
            json={"deck_id": deck_id, "opponent_deck_id": deck_id},
        )
    ).json()["id"]

    tree = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    ).json()
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    opponent_zones_before = opening["state"]["opponent_zones"]

    draw_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": opening["id"], "action": {"type": "draw", "target": "self"}},
    )
    assert draw_res.status_code == 200
    node = draw_res.json()
    assert node["state"]["opponent_zones"] == opponent_zones_before

    shuffle_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": node["id"], "action": {"type": "shuffle", "target": "self"}},
    )
    assert shuffle_res.status_code == 200
    node2 = shuffle_res.json()
    assert node2["state"]["opponent_zones"] == opponent_zones_before


@pytest.mark.asyncio
async def test_opponent_target_draw_label_and_self_zones_unchanged(
    client: AsyncClient, db_session
) -> None:
    db_session.add(
        Card(
            id="card-p-draw",
            name="Primary Draw Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    db_session.add(
        Card(
            id="card-o-draw",
            name="Opponent Draw Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    await db_session.commit()

    _user, session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "opp_draw@example.com",
        "opp_draw_sub",
        [{"card_id": "card-p-draw", "quantity": 10, "board": "main"}],
        [{"card_id": "card-o-draw", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    self_hand_before = list(opening["state"]["hand"])
    self_library_before = list(opening["state"]["library"])
    self_battlefield_before = list(opening["state"]["battlefield"])
    self_graveyard_before = list(opening["state"]["graveyard"])
    self_exile_before = list(opening["state"]["exile"])
    opponent_hand_before = list(opening["state"]["opponent_zones"]["hand"])
    opponent_library_before = list(opening["state"]["opponent_zones"]["library"])

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": opening["id"],
            "action": {"type": "draw", "target": "opponent"},
        },
    )
    assert response.status_code == 200
    node = response.json()
    assert node["label"] == "Opponent: Drew Opponent Draw Card"
    assert node["state"]["opponent_zones"]["hand"] == opponent_hand_before + [
        opponent_library_before[0]
    ]
    assert node["state"]["opponent_zones"]["library"] == opponent_library_before[1:]

    # An opponent-target action must never touch the self side.
    assert node["state"]["hand"] == self_hand_before
    assert node["state"]["library"] == self_library_before
    assert node["state"]["battlefield"] == self_battlefield_before
    assert node["state"]["graveyard"] == self_graveyard_before
    assert node["state"]["exile"] == self_exile_before


@pytest.mark.asyncio
async def test_opponent_target_play_land_label(client: AsyncClient, db_session) -> None:
    db_session.add(
        Card(
            id="card-p-pl",
            name="Primary PL Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    db_session.add(
        Card(
            id="card-o-pl",
            name="Opponent PL Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    await db_session.commit()

    _user, session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "opp_pl@example.com",
        "opp_pl_sub",
        [{"card_id": "card-p-pl", "quantity": 10, "board": "main"}],
        [{"card_id": "card-o-pl", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    opponent_card_id = opening["state"]["opponent_zones"]["hand"][0]

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": opening["id"],
            "action": {
                "type": "play_land",
                "card_id": opponent_card_id,
                "target": "opponent",
            },
        },
    )
    assert response.status_code == 200
    node = response.json()
    assert node["label"] == "Opponent: Played Opponent PL Card"
    assert node["state"]["opponent_zones"]["battlefield"] == [opponent_card_id]
    # All copies share one card_id, so check count, not membership.
    assert (
        len(node["state"]["opponent_zones"]["hand"])
        == len(opening["state"]["opponent_zones"]["hand"]) - 1
    )


@pytest.mark.asyncio
async def test_opponent_target_cast_label(client: AsyncClient, db_session) -> None:
    db_session.add(
        Card(
            id="card-p-cast",
            name="Primary Cast Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    db_session.add(
        Card(
            id="card-o-cast",
            name="Opponent Cast Card",
            type_line="Creature",
            produced_mana=[],
        )
    )
    await db_session.commit()

    _user, session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "opp_cast@example.com",
        "opp_cast_sub",
        [{"card_id": "card-p-cast", "quantity": 10, "board": "main"}],
        [{"card_id": "card-o-cast", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    opponent_card_id = opening["state"]["opponent_zones"]["hand"][0]

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": opening["id"],
            "action": {
                "type": "cast",
                "card_id": opponent_card_id,
                "target": "opponent",
            },
        },
    )
    assert response.status_code == 200
    node = response.json()
    assert node["label"] == "Opponent: Cast Opponent Cast Card"
    assert node["state"]["opponent_zones"]["battlefield"] == [opponent_card_id]
    assert (
        len(node["state"]["opponent_zones"]["hand"])
        == len(opening["state"]["opponent_zones"]["hand"]) - 1
    )


@pytest.mark.asyncio
async def test_opponent_target_move_zone_label(client: AsyncClient, db_session) -> None:
    db_session.add(
        Card(
            id="card-p-mz",
            name="Primary MZ Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    db_session.add(
        Card(
            id="card-o-mz",
            name="Opponent MZ Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    await db_session.commit()

    _user, session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "opp_mz@example.com",
        "opp_mz_sub",
        [{"card_id": "card-p-mz", "quantity": 10, "board": "main"}],
        [{"card_id": "card-o-mz", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    opponent_card_id = opening["state"]["opponent_zones"]["hand"][0]

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": opening["id"],
            "action": {
                "type": "move_zone",
                "card_id": opponent_card_id,
                "from_zone": "hand",
                "to_zone": "graveyard",
                "target": "opponent",
            },
        },
    )
    assert response.status_code == 200
    node = response.json()
    assert node["label"] == "Opponent: Moved Opponent MZ Card from hand to graveyard"
    assert node["state"]["opponent_zones"]["graveyard"] == [opponent_card_id]
    assert (
        len(node["state"]["opponent_zones"]["hand"])
        == len(opening["state"]["opponent_zones"]["hand"]) - 1
    )


@pytest.mark.asyncio
async def test_opponent_target_shuffle_label(client: AsyncClient, db_session) -> None:
    db_session.add(
        Card(
            id="card-p-sh",
            name="Primary SH Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    db_session.add(
        Card(
            id="card-o-sh",
            name="Opponent SH Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    await db_session.commit()

    _user, session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "opp_sh@example.com",
        "opp_sh_sub",
        [{"card_id": "card-p-sh", "quantity": 10, "board": "main"}],
        [{"card_id": "card-o-sh", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    opponent_library_before = list(opening["state"]["opponent_zones"]["library"])

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": opening["id"],
            "action": {"type": "shuffle", "target": "opponent"},
        },
    )
    assert response.status_code == 200
    node = response.json()
    assert node["label"] == "Opponent: Shuffled library"
    assert sorted(node["state"]["opponent_zones"]["library"]) == sorted(
        opponent_library_before
    )
    assert len(node["state"]["opponent_zones"]["library"]) == len(
        opponent_library_before
    )
    assert node["state"]["hand"] == opening["state"]["hand"]


@pytest.mark.asyncio
async def test_self_target_action_in_two_deck_session_label_unprefixed(
    client: AsyncClient, db_session
) -> None:
    db_session.add(
        Card(
            id="card-p-self",
            name="Primary Self Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    db_session.add(
        Card(
            id="card-o-self",
            name="Opponent Self Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    await db_session.commit()

    _user, session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "self_2deck@example.com",
        "self_2deck_sub",
        [{"card_id": "card-p-self", "quantity": 10, "board": "main"}],
        [{"card_id": "card-o-self", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": opening["id"], "action": {"type": "draw"}},  # target: self
    )
    assert response.status_code == 200
    node = response.json()
    assert node["label"] == "Drew Primary Self Card"
    assert not node["label"].startswith("Opponent:")


@pytest.mark.asyncio
async def test_opponent_target_draw_with_empty_opponent_library_does_not_crash(
    client: AsyncClient, db_session
) -> None:
    db_session.add(
        Card(
            id="card-p-empty",
            name="Primary Empty Card",
            type_line="Land",
            produced_mana=["C"],
        )
    )
    await db_session.commit()

    _user, session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "opp_empty_draw@example.com",
        "opp_empty_draw_sub",
        [{"card_id": "card-p-empty", "quantity": 10, "board": "main"}],
        [],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    assert opening["state"]["opponent_zones"]["hand"] == []

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": opening["id"],
            "action": {"type": "draw", "target": "opponent"},
        },
    )
    assert response.status_code == 200
    node = response.json()
    assert node["state"]["opponent_zones"]["hand"] == []
    assert node["label"] == "Opponent: Tried to draw with an empty library"


@pytest.mark.asyncio
async def test_opponent_target_zone_action_without_opponent_deck_returns_400(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "no_opp_deck@example.com", "no_opp_deck_sub"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": root["id"],
            "action": {"type": "shuffle", "target": "opponent"},
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "This session has no opponent deck"


@pytest.mark.asyncio
async def test_opening_hand_asymmetry_opponent_empty_library(
    client: AsyncClient, db_session
) -> None:
    db_session.add(
        Card(
            id="card-p-asym1", name="Asym1 Card", type_line="Land", produced_mana=["C"]
        )
    )
    await db_session.commit()

    _user, _session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "asym_opp_empty@example.com",
        "asym_opp_empty_sub",
        [{"card_id": "card-p-asym1", "quantity": 10, "board": "main"}],
        [],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    assert opening["state"]["opponent_zones"]["hand"] == []
    assert len(opening["state"]["hand"]) == 7
    assert opening["label"] == "Drew opening hands (7 cards; opponent drew 0 cards)"


@pytest.mark.asyncio
async def test_opening_hand_asymmetry_both_libraries_one_card(
    client: AsyncClient, db_session
) -> None:
    db_session.add(
        Card(id="card-p-one", name="One P Card", type_line="Land", produced_mana=["C"])
    )
    db_session.add(
        Card(id="card-o-one", name="One O Card", type_line="Land", produced_mana=["C"])
    )
    await db_session.commit()

    _user, _session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "asym_one_each@example.com",
        "asym_one_each_sub",
        [{"card_id": "card-p-one", "quantity": 1, "board": "main"}],
        [{"card_id": "card-o-one", "quantity": 1, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    assert len(opening["state"]["hand"]) == 1
    assert len(opening["state"]["opponent_zones"]["hand"]) == 1
    assert opening["label"] == "Drew opening hands (1 card; opponent drew 1 card)"


@pytest.mark.asyncio
async def test_opening_hand_asymmetry_primary_empty_opponent_full(
    client: AsyncClient, db_session
) -> None:
    db_session.add(
        Card(
            id="card-o-full", name="Full O Card", type_line="Land", produced_mana=["C"]
        )
    )
    await db_session.commit()

    _user, _session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "asym_primary_empty@example.com",
        "asym_primary_empty_sub",
        [],
        [{"card_id": "card-o-full", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    # Updated node-creation guard: the opponent's dealt hand alone must still
    # produce the combined opening-hand node, even with an empty self hand.
    opening_nodes = [n for n in tree["nodes"] if n["parent_id"] == root["id"]]
    assert len(opening_nodes) == 1
    opening = opening_nodes[0]
    assert opening["state"]["hand"] == []
    assert len(opening["state"]["opponent_zones"]["hand"]) == 7
    assert opening["label"] == "Drew opening hands (0 cards; opponent drew 7 cards)"


@pytest.mark.asyncio
async def test_action_against_pre_3d_state_missing_opponent_zones_key(
    client: AsyncClient, db_session
) -> None:
    """
    Simulates a genuinely pre-3d row (hand-built `state` dict with no
    `opponent_zones` key at all — no session created through this phase's
    code can produce that shape) and confirms an action against it still
    succeeds, defaulting to `opponent_zones: null`.
    """
    user = User(email="pre3d@example.com", google_sub="pre3d_sub")
    db_session.add(user)
    db_session.add(
        Card(id="card-pre3d", name="Pre3D Card", type_line="Land", produced_mana=["C"])
    )
    await db_session.commit()
    await db_session.refresh(user)

    deck_id = await _make_deck_for_user(
        client,
        db_session,
        user,
        "Pre3D Deck",
        [{"card_id": "card-pre3d", "quantity": 2, "board": "main"}],
    )

    session = GoldfishSession(deck_id=deck_id, user_id=user.id, name="Pre-3d session")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    node = GoldfishNode(
        session_id=session.id,
        parent_id=None,
        label="Game start",
        order_index=0,
        trackers={},
        state={
            "library": ["card-pre3d", "card-pre3d"],
            "hand": [],
            "battlefield": [],
            "graveyard": [],
            "exile": [],
            "life_total": 20,
            "opponent_life_total": 20,
            # No "opponent_zones" key at all — this is the point of the test.
        },
    )
    db_session.add(node)
    await db_session.commit()
    await db_session.refresh(node)

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session.id}/nodes",
        json={"parent_id": node.id, "action": {"type": "draw"}},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["state"]["hand"] == ["card-pre3d"]
    assert result["state"]["opponent_zones"] is None


@pytest.mark.asyncio
async def test_state_dict_has_ten_keys_including_mana_spent(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_cards(
        client, db_session, "keys8@example.com", "keys8_sub"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    assert set(root["state"].keys()) == {
        "library",
        "hand",
        "battlefield",
        "graveyard",
        "exile",
        "life_total",
        "opponent_life_total",
        "opponent_zones",
        "mana_spent",
        "opponent_mana_spent",
    }


@pytest.mark.asyncio
async def test_next_turn_never_touches_opponent_zones_in_two_deck_session(
    client: AsyncClient, db_session
) -> None:
    db_session.add(
        Card(id="card-t2d", name="T2D Card", type_line="Land", produced_mana=["C"])
    )
    await db_session.commit()

    _user, session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "turn2deck@example.com",
        "turn2deck_sub",
        [{"card_id": "card-t2d", "quantity": 10, "board": "main"}],
        [{"card_id": "card-t2d", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    opponent_zones_before = opening["state"]["opponent_zones"]

    turn_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": opening["id"], "action": {"type": "next_turn"}},
    )
    assert turn_res.status_code == 200
    node = turn_res.json()
    assert node["state"]["opponent_zones"] == opponent_zones_before


# --- Phase 8: total mana spent tracker -------------------------------------


def test_gamestate_backfills_mana_spent_for_missing_keys():
    """A stored state dict from before Phase 8 has neither key at all; pydantic
    must default both to 0, same zero-migration mechanism 3b/3d relied on."""
    state = GameState(
        library=[],
        hand=[],
        battlefield=[],
        graveyard=[],
        exile=[],
        life_total=20,
        opponent_life_total=20,
    )
    assert state.mana_spent == 0
    assert state.opponent_mana_spent == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "card_id,expected_cmc",
    [
        ("mana-generic", 2),  # {2}
        ("mana-color", 1),  # {R}
        ("mana-hybrid", 1),  # {G/U}
        ("mana-phyrexian", 1),  # {G/P}
        ("mana-x", 1),  # {X}{R} -> X contributes 0, R contributes 1
    ],
)
async def test_cast_increments_mana_spent_by_cmc(
    client: AsyncClient, db_session, card_id, expected_cmc
) -> None:
    _user, deck_id = await _make_deck_with_mana_cards(
        client, db_session, f"mana_{card_id}@example.com", f"mana_{card_id}_sub"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)
    assert root["state"]["mana_spent"] == 0

    moved = await _move_to_hand(client, session_id, root["id"], card_id)
    cast_node = await _cast(client, session_id, moved["id"], card_id)

    assert cast_node["state"]["mana_spent"] == expected_cmc
    assert cast_node["state"]["opponent_mana_spent"] == 0


@pytest.mark.asyncio
async def test_cast_accumulates_mana_spent_across_multiple_casts(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_mana_cards(
        client, db_session, "mana_accum@example.com", "mana_accum_sub"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    moved1 = await _move_to_hand(client, session_id, root["id"], "mana-generic")
    cast1 = await _cast(client, session_id, moved1["id"], "mana-generic")
    assert cast1["state"]["mana_spent"] == 2

    moved2 = await _move_to_hand(client, session_id, cast1["id"], "mana-color")
    cast2 = await _cast(client, session_id, moved2["id"], "mana-color")
    assert cast2["state"]["mana_spent"] == 3  # 2 + 1


@pytest.mark.asyncio
async def test_cast_opponent_target_increments_opponent_mana_spent_only(
    client: AsyncClient, db_session
) -> None:
    db_session.add(
        Card(
            id="card-p-mana",
            name="Primary Mana Card",
            type_line="Land",
            mana_cost="",
            produced_mana=["C"],
        )
    )
    db_session.add(
        Card(
            id="card-o-mana",
            name="Opponent Mana Card",
            type_line="Creature",
            mana_cost="{3}{G}",
            produced_mana=[],
        )
    )
    await db_session.commit()

    _user, session_id, tree = await _make_two_deck_session(
        client,
        db_session,
        "opp_mana@example.com",
        "opp_mana_sub",
        [{"card_id": "card-p-mana", "quantity": 10, "board": "main"}],
        [{"card_id": "card-o-mana", "quantity": 10, "board": "main"}],
    )
    root = next(n for n in tree["nodes"] if n["parent_id"] is None)
    opening = next(n for n in tree["nodes"] if n["parent_id"] == root["id"])
    opponent_card_id = opening["state"]["opponent_zones"]["hand"][0]

    cast_node = await _cast(
        client, session_id, opening["id"], opponent_card_id, target="opponent"
    )

    assert cast_node["state"]["opponent_mana_spent"] == 4  # {3}{G}
    assert cast_node["state"]["mana_spent"] == 0


@pytest.mark.asyncio
async def test_play_land_does_not_change_mana_spent(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_mana_cards(
        client, db_session, "mana_land@example.com", "mana_land_sub"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    moved = await _move_to_hand(client, session_id, root["id"], "mana-land")
    play_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": moved["id"],
            "action": {"type": "play_land", "card_id": "mana-land"},
        },
    )
    assert play_res.status_code == 200
    node = play_res.json()
    assert node["state"]["mana_spent"] == 0
    assert node["state"]["opponent_mana_spent"] == 0


@pytest.mark.asyncio
async def test_other_actions_carry_mana_spent_forward_unchanged(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_deck_with_mana_cards(
        client, db_session, "mana_carry@example.com", "mana_carry_sub"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    root = await _get_root(client, session_id)

    moved = await _move_to_hand(client, session_id, root["id"], "mana-generic")
    cast_node = await _cast(client, session_id, moved["id"], "mana-generic")
    assert cast_node["state"]["mana_spent"] == 2

    # draw
    draw_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": cast_node["id"], "action": {"type": "draw"}},
    )
    assert draw_res.json()["state"]["mana_spent"] == 2

    # move_zone
    battlefield_card_id = cast_node["state"]["battlefield"][0]
    move_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": cast_node["id"],
            "action": {
                "type": "move_zone",
                "card_id": battlefield_card_id,
                "from_zone": "battlefield",
                "to_zone": "graveyard",
            },
        },
    )
    assert move_res.json()["state"]["mana_spent"] == 2

    # set_life
    life_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": cast_node["id"],
            "action": {"type": "set_life", "life_total": 15},
        },
    )
    assert life_res.json()["state"]["mana_spent"] == 2

    # shuffle
    shuffle_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": cast_node["id"], "action": {"type": "shuffle"}},
    )
    assert shuffle_res.json()["state"]["mana_spent"] == 2

    # next_turn
    turn_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": cast_node["id"], "action": {"type": "next_turn"}},
    )
    assert turn_res.json()["state"]["mana_spent"] == 2
