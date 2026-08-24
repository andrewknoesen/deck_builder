import pytest
from app.core.config import settings
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy import text


async def _make_user_and_deck(client: AsyncClient, db_session, email: str, sub: str):
    user = User(email=email, google_sub=sub, full_name="Test User")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    deck_res = await client.post(
        f"{settings.API_V1_STR}/decks/",
        json={"title": "Goldfish Deck", "user_id": user.id, "cards": []},
    )
    assert deck_res.status_code == 200
    return user, deck_res.json()["id"]


@pytest.mark.asyncio
async def test_create_and_list_sessions(client: AsyncClient, db_session) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish1@example.com", "gf_sub_1"
    )

    create_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions",
        json={"deck_id": deck_id, "name": "Session One"},
    )
    assert create_res.status_code == 200
    session_data = create_res.json()
    assert session_data["name"] == "Session One"
    assert session_data["deck_id"] == deck_id

    list_res = await client.get(
        f"{settings.API_V1_STR}/goldfish/sessions", params={"deck_id": deck_id}
    )
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_data["id"]


@pytest.mark.asyncio
async def test_delete_deck_with_goldfish_session_cascades(
    client: AsyncClient, db_session
) -> None:
    """
    Regression test: deck_id/opponent_deck_id had no ON DELETE rule, so
    Postgres's default RESTRICT turned deleting any deck with a practice
    session into an unhandled IntegrityError (500) instead of cascading.
    The test DB is SQLite, which ignores FK constraints unless explicitly
    turned on per-connection - do that here (scoped to this test's own
    connection) so the assertion actually exercises ondelete=CASCADE
    instead of trivially passing because nothing enforces the FK.
    """
    await db_session.execute(text("PRAGMA foreign_keys=ON"))

    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish_delete@example.com", "gf_sub_delete"
    )
    session_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions",
        json={"deck_id": deck_id, "name": "To be orphaned"},
    )
    assert session_res.status_code == 200
    session_id = session_res.json()["id"]

    delete_res = await client.delete(f"{settings.API_V1_STR}/decks/{deck_id}")
    assert delete_res.status_code == 200

    list_res = await client.get(
        f"{settings.API_V1_STR}/goldfish/sessions", params={"deck_id": deck_id}
    )
    assert session_id not in [s["id"] for s in list_res.json()]


@pytest.mark.asyncio
async def test_create_session_default_name(client: AsyncClient, db_session) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish_default@example.com", "gf_sub_default"
    )

    create_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
    )
    assert create_res.status_code == 200
    assert "Goldfish Deck" in create_res.json()["name"]


@pytest.mark.asyncio
async def test_create_session_rejects_deck_owned_by_another_user(
    client: AsyncClient, db_session
) -> None:
    _owner, deck_id = await _make_user_and_deck(
        client, db_session, "gf_owner@example.com", "gf_owner_sub"
    )
    other = User(email="gf_other@example.com", google_sub="gf_other_sub")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    app.dependency_overrides[get_current_user] = lambda: other
    try:
        response = await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions",
            json={"deck_id": deck_id, "name": "Hijack"},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_session_tree_starts_with_auto_created_root(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish2@example.com", "gf_sub_2"
    )
    create_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
    )
    session_id = create_res.json()["id"]

    tree_res = await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    assert tree_res.status_code == 200
    data = tree_res.json()
    assert data["session"]["id"] == session_id
    assert len(data["nodes"]) == 1

    root = data["nodes"][0]
    assert root["label"] == "Game start"
    assert root["parent_id"] is None
    assert root["state"]["library"] == []  # this test deck has no cards
    assert root["state"]["life_total"] == 20  # no format set -> not commander-like


@pytest.mark.asyncio
async def test_add_root_and_branching_nodes(client: AsyncClient, db_session) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish3@example.com", "gf_sub_3"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]
    auto_root_id = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    ).json()["nodes"][0]["id"]

    root_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": auto_root_id, "label": "Turn 1: play a land"},
    )
    assert root_res.status_code == 200
    root = root_res.json()
    assert root["parent_id"] == auto_root_id
    assert root["order_index"] == 0

    child_a = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
            json={"parent_id": root["id"], "label": "Turn 2: cast Llanowar Elves"},
        )
    ).json()
    assert child_a["parent_id"] == root["id"]
    assert child_a["order_index"] == 0

    # A second child under the same parent is a branch, not an overwrite.
    child_b = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
            json={"parent_id": root["id"], "label": "Turn 2: cast Sol Ring instead"},
        )
    ).json()
    assert child_b["parent_id"] == root["id"]
    assert child_b["order_index"] == 1

    tree_res = await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    nodes = tree_res.json()["nodes"]
    assert len(nodes) == 4
    assert {n["id"] for n in nodes} == {
        auto_root_id,
        root["id"],
        child_a["id"],
        child_b["id"],
    }


@pytest.mark.asyncio
async def test_node_trackers_are_a_generic_opaque_snapshot(
    client: AsyncClient, db_session
) -> None:
    """Trackers are a free-form key->value map (life, poison, storm count,
    whatever) — the backend just stores whatever snapshot it's given, no
    fixed schema, no inheritance logic. The frontend decides what to carry
    forward from the selected node into the next one."""
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish_trackers@example.com", "gf_sub_trackers"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    root_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"label": "Start", "trackers": {"life": 40}},
    )
    assert root_res.status_code == 200
    root = root_res.json()
    assert root["trackers"] == {"life": 40}

    child_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={
            "parent_id": root["id"],
            "label": "Took a hit, played a poison counter card",
            "trackers": {"life": 37, "poison": 1},
        },
    )
    assert child_res.status_code == 200
    assert child_res.json()["trackers"] == {"life": 37, "poison": 1}

    no_tracker_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": root["id"], "label": "no trackers given"},
    )
    assert no_tracker_res.status_code == 200
    assert no_tracker_res.json()["trackers"] == {}


@pytest.mark.asyncio
async def test_add_node_to_nonexistent_parent_404(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish4@example.com", "gf_sub_4"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    response = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"parent_id": 999999, "label": "orphan"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_node_cascades_to_descendants_only(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish5@example.com", "gf_sub_5"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    async def add(parent_id, label):
        res = await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
            json={"parent_id": parent_id, "label": label},
        )
        return res.json()

    auto_root_id = (
        await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    ).json()["nodes"][0]["id"]

    root = await add(auto_root_id, "root")
    branch_to_prune = await add(root["id"], "prune me")
    grandchild = await add(branch_to_prune["id"], "should also die")
    surviving_sibling = await add(root["id"], "keep me")

    delete_res = await client.delete(
        f"{settings.API_V1_STR}/goldfish/nodes/{branch_to_prune['id']}"
    )
    assert delete_res.status_code == 200
    assert delete_res.json()["deleted"] == 2

    tree_res = await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    remaining_ids = {n["id"] for n in tree_res.json()["nodes"]}
    assert remaining_ids == {auto_root_id, root["id"], surviving_sibling["id"]}
    assert grandchild["id"] not in remaining_ids
    assert branch_to_prune["id"] not in remaining_ids


@pytest.mark.asyncio
async def test_cannot_access_another_users_session(
    client: AsyncClient, db_session
) -> None:
    _owner, deck_id = await _make_user_and_deck(
        client, db_session, "gf_owner2@example.com", "gf_owner_sub2"
    )
    other = User(email="gf_other2@example.com", google_sub="gf_other_sub2")
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    app.dependency_overrides[get_current_user] = lambda: other
    try:
        tree_res = await client.get(
            f"{settings.API_V1_STR}/goldfish/sessions/{session_id}"
        )
        assert tree_res.status_code == 403

        add_res = await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
            json={"label": "sneaky"},
        )
        assert add_res.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_session_outcome_set_and_clear(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish_outcome@example.com", "gf_sub_outcome"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    # New sessions start with no recorded outcome.
    tree_res = await client.get(f"{settings.API_V1_STR}/goldfish/sessions/{session_id}")
    assert tree_res.json()["session"]["outcome"] is None

    set_res = await client.patch(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}",
        json={"outcome": "win"},
    )
    assert set_res.status_code == 200
    assert set_res.json()["outcome"] == "win"

    # Freely editable — no lock/finalize concept.
    update_res = await client.patch(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}",
        json={"outcome": "loss"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["outcome"] == "loss"

    clear_res = await client.patch(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}",
        json={"outcome": None},
    )
    assert clear_res.status_code == 200
    assert clear_res.json()["outcome"] is None


@pytest.mark.asyncio
async def test_update_session_outcome_rejects_invalid_value(
    client: AsyncClient, db_session
) -> None:
    _user, deck_id = await _make_user_and_deck(
        client, db_session, "goldfish_outcome_invalid@example.com", "gf_sub_outcome_inv"
    )
    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    response = await client.patch(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}",
        json={"outcome": "tie"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_session_outcome_ownership(
    client: AsyncClient, db_session
) -> None:
    _owner, deck_id = await _make_user_and_deck(
        client, db_session, "gf_owner_outcome@example.com", "gf_owner_outcome_sub"
    )
    other = User(
        email="gf_other_outcome@example.com", google_sub="gf_other_outcome_sub"
    )
    db_session.add(other)
    await db_session.commit()
    await db_session.refresh(other)

    session_id = (
        await client.post(
            f"{settings.API_V1_STR}/goldfish/sessions", json={"deck_id": deck_id}
        )
    ).json()["id"]

    app.dependency_overrides[get_current_user] = lambda: other
    try:
        response = await client.patch(
            f"{settings.API_V1_STR}/goldfish/sessions/{session_id}",
            json={"outcome": "win"},
        )
        assert response.status_code == 403
    finally:
        # Only remove the get_current_user override here, not .clear() — this
        # test still has a DB-dependent call below, and .clear() would also
        # wipe the client fixture's get_db override (a real bug hit and fixed
        # in Phase 3b, per PLAN.md).
        del app.dependency_overrides[get_current_user]

    not_found_res = await client.patch(
        f"{settings.API_V1_STR}/goldfish/sessions/999999",
        json={"outcome": "win"},
    )
    assert not_found_res.status_code == 404
