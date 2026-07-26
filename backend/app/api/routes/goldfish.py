from typing import List, Optional

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.deck import Deck
from app.models.goldfish import (
    GoldfishNode,
    GoldfishNodeCreate,
    GoldfishNodePublic,
    GoldfishSession,
    GoldfishSessionCreate,
    GoldfishSessionPublic,
)
from app.models.user import User
from app.schemas.goldfish import GoldfishSessionTree
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

router = APIRouter()


async def _get_owned_session(
    session_id: int, db: AsyncSession, current_user: User
) -> GoldfishSession:
    result = await db.execute(
        select(GoldfishSession).where(GoldfishSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return session


@router.post("/sessions", response_model=GoldfishSessionPublic)
async def create_session(
    session_in: GoldfishSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new goldfishing session for a deck.
    """
    result = await db.execute(select(Deck).where(Deck.id == session_in.deck_id))
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    db_session = GoldfishSession(
        deck_id=session_in.deck_id,
        user_id=current_user.id,
        name=session_in.name or f"{deck.title} practice session",
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


@router.get("/sessions", response_model=List[GoldfishSessionPublic])
async def list_sessions(
    deck_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List goldfishing sessions for a deck (owned by the requesting user).
    """
    result = await db.execute(
        select(GoldfishSession)
        .where(GoldfishSession.deck_id == deck_id)
        .where(GoldfishSession.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=GoldfishSessionTree)
async def get_session_tree(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full tree for a session: the session plus every node, flat — the client
    reconstructs the tree from each node's parent_id.
    """
    session = await _get_owned_session(session_id, db, current_user)

    result = await db.execute(
        select(GoldfishNode).where(GoldfishNode.session_id == session_id)
    )
    nodes = result.scalars().all()
    return GoldfishSessionTree(session=session, nodes=nodes)


@router.post("/sessions/{session_id}/nodes", response_model=GoldfishNodePublic)
async def add_node(
    session_id: int,
    node_in: GoldfishNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a node under `parent_id` (omit to add a top-level/root node). Adding a
    second child under a node that already has one child is what creates a
    branch — the client renders siblings side by side rather than overwriting.
    """
    await _get_owned_session(session_id, db, current_user)

    if node_in.parent_id is not None:
        parent_result = await db.execute(
            select(GoldfishNode)
            .where(GoldfishNode.id == node_in.parent_id)
            .where(GoldfishNode.session_id == session_id)
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Parent node not found")

    siblings_result = await db.execute(
        select(GoldfishNode)
        .where(GoldfishNode.session_id == session_id)
        .where(GoldfishNode.parent_id == node_in.parent_id)
    )
    order_index = len(siblings_result.scalars().all())

    db_node = GoldfishNode(
        session_id=session_id,
        parent_id=node_in.parent_id,
        label=node_in.label,
        turn_number=node_in.turn_number,
        order_index=order_index,
        trackers=node_in.trackers or {},
    )
    db.add(db_node)
    await db.commit()
    await db.refresh(db_node)
    return db_node


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Prune a branch: deletes the node and every descendant.
    """
    result = await db.execute(select(GoldfishNode).where(GoldfishNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    await _get_owned_session(node.session_id, db, current_user)

    all_nodes_result = await db.execute(
        select(GoldfishNode).where(GoldfishNode.session_id == node.session_id)
    )
    all_nodes = all_nodes_result.scalars().all()
    children_by_parent: dict[Optional[int], list[GoldfishNode]] = {}
    for n in all_nodes:
        children_by_parent.setdefault(n.parent_id, []).append(n)

    to_delete: list[GoldfishNode] = []
    queue = [node]
    while queue:
        current = queue.pop()
        to_delete.append(current)
        queue.extend(children_by_parent.get(current.id, []))

    for n in to_delete:
        await db.delete(n)
    await db.commit()
    return {"status": "ok", "deleted": len(to_delete)}
