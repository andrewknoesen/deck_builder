from unittest.mock import AsyncMock

import pytest
from app.core.config import settings
from app.main import app
from app.models.card import Card
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


async def _make_deck_with_many_cards(client: AsyncClient, db_session, email: str, sub: str):
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
    assert node["label"] == f"Drew {'Card A' if library_before[0] == 'card-a' else 'Card B'}"


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
