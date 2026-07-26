import pytest
from app.core.config import settings
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from httpx import AsyncClient


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
async def test_get_session_tree_starts_empty(client: AsyncClient, db_session) -> None:
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
    assert data["nodes"] == []


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

    root_res = await client.post(
        f"{settings.API_V1_STR}/goldfish/sessions/{session_id}/nodes",
        json={"label": "Turn 1: play a land"},
    )
    assert root_res.status_code == 200
    root = root_res.json()
    assert root["parent_id"] is None
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
    assert len(nodes) == 3
    assert {n["id"] for n in nodes} == {root["id"], child_a["id"], child_b["id"]}


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

    root = await add(None, "root")
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
    assert remaining_ids == {root["id"], surviving_sibling["id"]}
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
