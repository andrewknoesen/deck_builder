import pytest
from app.api.deps import get_current_user
from app.core.config import settings
from app.main import app
from app.models.user import User
from httpx import AsyncClient


async def _make_user_and_deck(
    client: AsyncClient,
    db_session,
    email: str,
    sub: str,
    deck_format: str | None = None,
):
    user = User(email=email, google_sub=sub, full_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    deck_res = await client.post(
        f"{settings.API_V1_STR}/decks/",
        json={
            "title": "Analytics Deck",
            "format": deck_format,
            "user_id": user.id,
            "cards": [],
        },
    )
    assert deck_res.status_code == 200
    return user, deck_res.json()["id"]


async def _make_deck_for_user(
    client: AsyncClient, user: User, title: str, deck_format: str | None = None
):
    deck_res = await client.post(
        f"{settings.API_V1_STR}/decks/",
        json={"title": title, "format": deck_format, "user_id": user.id, "cards": []},
    )
    assert deck_res.status_code == 200
    return deck_res.json()["id"]


async def _create_session(client: AsyncClient, deck_id: int, opponent_deck_id=None):
    payload = {"deck_id": deck_id}
    if opponent_deck_id is not None:
        payload["opponent_deck_id"] = opponent_deck_id
    res = await client.post(f"{settings.API_V1_STR}/goldfish/sessions", json=payload)
    assert res.status_code == 200
    return res.json()["id"]


async def _add_node(client: AsyncClient, session_id: int, parent_id, turn_number: int):
    res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": parent_id,
            "label": f"Turn {turn_number}",
            "turn_number": turn_number,
        },
    )
    assert res.status_code == 200
    return res.json()


async def _get_analytics(client: AsyncClient, deck_id: int):
    return await client.get(
        f"{settings.API_V1_STR}/goldfish/analytics", params={"deck_id": deck_id}
    )


@pytest.mark.asyncio
async def test_analytics_zero_sessions(client: AsyncClient, db_session) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "analytics_zero@example.com", "an_sub_zero"
    )

    response = await _get_analytics(client, deck_id)
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "session_count": 0,
        "sessions_with_outcome": 0,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "win_rate": None,
        "average_max_turn": None,
        "two_deck_session_ratio": None,
    }


@pytest.mark.asyncio
async def test_analytics_win_rate_excludes_unrecorded_sessions(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "analytics_outcomes@example.com", "an_sub_outcomes"
    )

    win_id = await _create_session(client, deck_id)
    loss_id = await _create_session(client, deck_id)
    draw_id = await _create_session(client, deck_id)
    await _create_session(client, deck_id)  # left unrecorded

    for session_id, outcome in ((win_id, "win"), (loss_id, "loss"), (draw_id, "draw")):
        patch_res = await client.patch(
            f"{settings.API_V1_STR}/goldfish/sessions/{session_id}",
            json={"outcome": outcome},
        )
        assert patch_res.status_code == 200

    response = await _get_analytics(client, deck_id)
    assert response.status_code == 200
    data = response.json()
    assert data["session_count"] == 4
    assert data["sessions_with_outcome"] == 3
    assert data["wins"] == 1
    assert data["losses"] == 1
    assert data["draws"] == 1
    assert data["win_rate"] == pytest.approx(1 / 3)


@pytest.mark.asyncio
async def test_analytics_average_max_turn_reads_whole_tree_not_first_branch(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "analytics_turns@example.com", "an_sub_turns"
    )

    # Session A: branches off a shared node — one short branch (turn 2), one
    # long, later-explored branch (turn 4). Whole-tree max should be 4, not
    # whatever the first-created branch reaches.
    session_a = await _create_session(client, deck_id)
    root_id = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_a}")
    ).json()["nodes"][0]["id"]
    t1 = await _add_node(client, session_a, root_id, 1)
    short_branch = await _add_node(client, session_a, t1["id"], 2)
    long_branch_t2 = await _add_node(client, session_a, t1["id"], 2)
    long_branch_t3 = await _add_node(client, session_a, long_branch_t2["id"], 3)
    await _add_node(client, session_a, long_branch_t3["id"], 4)
    assert short_branch["turn_number"] == 2  # short branch never advances further

    # Session B: reaches turn 2 only.
    session_b = await _create_session(client, deck_id)
    root_b_id = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_b}")
    ).json()["nodes"][0]["id"]
    await _add_node(client, session_b, root_b_id, 2)

    # Session C: no turn_number ever set anywhere — excluded from the average
    # entirely (not counted as 0).
    await _create_session(client, deck_id)

    response = await _get_analytics(client, deck_id)
    assert response.status_code == 200
    data = response.json()
    assert data["average_max_turn"] == pytest.approx((4 + 2) / 2)


@pytest.mark.asyncio
async def test_analytics_two_deck_session_ratio(
    client: AsyncClient, db_session
) -> None:
    user, deck_id = await _make_user_and_deck(
        client, db_session, "analytics_twodeck@example.com", "an_sub_twodeck"
    )
    opponent_deck_id = await _make_deck_for_user(client, user, "Opponent Deck")

    await _create_session(client, deck_id)
    await _create_session(client, deck_id)
    await _create_session(client, deck_id, opponent_deck_id=opponent_deck_id)

    response = await _get_analytics(client, deck_id)
    assert response.status_code == 200
    data = response.json()
    assert data["session_count"] == 3
    assert data["two_deck_session_ratio"] == pytest.approx(1 / 3)


@pytest.mark.asyncio
async def test_analytics_ownership(client: AsyncClient, db_session) -> None:
    _owner, deck_id = await _make_user_and_deck(
        client, db_session, "analytics_owner@example.com", "an_sub_owner"
    )
    other = User(email="analytics_other@example.com", google_sub="an_sub_other")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    app.dependency_overrides[get_current_user] = lambda: other
    try:
        response = await _get_analytics(client, deck_id)
        assert response.status_code == 403
    finally:
        # Only remove the get_current_user override here, not .clear() — this
        # test still has a DB-dependent call below, and .clear() would also
        # wipe the client fixture's get_db override (a real bug hit and fixed
        # in Phase 3b, per PLAN.md).
        del app.dependency_overrides[get_current_user]

    not_found_res = await _get_analytics(client, 999999)
    assert not_found_res.status_code == 404
