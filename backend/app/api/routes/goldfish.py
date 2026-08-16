from typing import List, Optional

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.card import Card
from app.models.deck import Deck
from app.models.goldfish import (
    GameState,
    GoldfishNode,
    GoldfishNodeCreate,
    GoldfishNodePublic,
    GoldfishSession,
    GoldfishSessionCreate,
    GoldfishSessionPublic,
)
from app.models.user import User
from app.schemas.goldfish import (
    GoldfishAnalyticsPublic,
    GoldfishSessionOutcomeUpdate,
    GoldfishSessionTree,
)
from app.services.goldfish import (
    apply_action,
    build_initial_state,
    draw_card,
    draw_opening_hand,
)
from app.services.goldfish_analytics import compute_deck_analytics
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
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
    Start a new goldfishing session for a deck, optionally paired against a
    second, opponent deck (Phase 3d two-deck goldfishing). Auto-creates a
    root node with freshly shuffled virtual libraries, then a single combined
    child node dealing the opening hand(s) (7 cards each, or fewer if a
    library is smaller) — every session begins ready to play, not with an
    empty hand waiting on manual draws.
    """
    result = await db.execute(
        select(Deck)
        .where(Deck.id == session_in.deck_id)
        .options(selectinload(Deck.cards))  # type: ignore[arg-type]
    )
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    opponent_deck: Optional[Deck] = None
    if session_in.opponent_deck_id is not None:
        opponent_result = await db.execute(
            select(Deck)
            .where(Deck.id == session_in.opponent_deck_id)
            .options(selectinload(Deck.cards))  # type: ignore[arg-type]
        )
        opponent_deck = opponent_result.scalar_one_or_none()
        if not opponent_deck:
            raise HTTPException(status_code=404, detail="Opponent deck not found")
        if opponent_deck.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        if opponent_deck.format != deck.format:
            raise HTTPException(
                status_code=400,
                detail="Opponent deck must be the same format as the primary deck",
            )

    db_session = GoldfishSession(
        deck_id=session_in.deck_id,
        opponent_deck_id=session_in.opponent_deck_id,
        user_id=current_user.id,
        name=session_in.name or f"{deck.title} practice session",
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)

    initial_state = build_initial_state(deck, opponent_deck)
    root_node = GoldfishNode(
        session_id=db_session.id,
        parent_id=None,
        label="Game start",
        order_index=0,
        trackers={},
        state=initial_state.model_dump(),
    )
    db.add(root_node)
    await db.commit()

    opening_state, opening_label = draw_opening_hand(initial_state)
    if opening_state.hand or (
        opening_state.opponent_zones and opening_state.opponent_zones.hand
    ):
        opening_node = GoldfishNode(
            session_id=db_session.id,
            parent_id=root_node.id,
            label=opening_label,
            order_index=0,
            trackers={},
            state=opening_state.model_dump(),
        )
        db.add(opening_node)
        await db.commit()

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


@router.patch("/sessions/{session_id}", response_model=GoldfishSessionPublic)
async def update_session_outcome(
    session_id: int,
    outcome_in: GoldfishSessionOutcomeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set, change, or clear a session's manually-recorded outcome
    (win/loss/draw/None). Session-level, not tied to any tree branch — there's
    no "end session" lock, this can be freely edited at any time, for both
    single-deck and two-deck sessions.
    """
    session = await _get_owned_session(session_id, db, current_user)
    session.outcome = outcome_in.outcome
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/analytics", response_model=GoldfishAnalyticsPublic)
async def get_analytics(
    deck_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregate goldfishing analytics across every session for a deck (owned by
    the requesting user) — win rate, average max turn reached, and two-deck
    session ratio.
    """
    deck_result = await db.execute(select(Deck).where(Deck.id == deck_id))
    deck = deck_result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return await compute_deck_analytics(db, deck_id, current_user.id)


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

    Two ways to add a node: a free-text note (`label`, optionally `trackers`),
    or a structured `action` (draw/play_land/cast/move_zone/set_life/shuffle/
    next_turn) applied to the parent's game state — the resulting state is
    snapshotted onto the new node and a human-readable label is generated
    unless one was given. `turn_number` carries forward from the parent node
    unless a `next_turn` action bumps it or the caller explicitly overrides it.
    `next_turn` also auto-draws a card for the turn, same as clicking Draw.
    """
    await _get_owned_session(session_id, db, current_user)

    parent_node = None
    if node_in.parent_id is not None:
        parent_result = await db.execute(
            select(GoldfishNode)
            .where(GoldfishNode.id == node_in.parent_id)
            .where(GoldfishNode.session_id == session_id)
        )
        parent_node = parent_result.scalar_one_or_none()
        if not parent_node:
            raise HTTPException(status_code=404, detail="Parent node not found")

    label = node_in.label
    new_state: Optional[dict] = None
    turn_number = node_in.turn_number
    if turn_number is None and parent_node is not None:
        turn_number = parent_node.turn_number

    if node_in.action is not None:
        if not parent_node or not parent_node.state:
            raise HTTPException(
                status_code=400,
                detail="Parent node has no game state to apply this action to",
            )
        parent_state = GameState(**parent_node.state)

        if node_in.action.type == "next_turn":
            turn_number = (parent_node.turn_number or 0) + 1
            drawn_state, drawn_card_id = draw_card(parent_state)
            new_state = drawn_state.model_dump()
            if drawn_card_id:
                name_result = await db.execute(
                    select(Card.name).where(Card.id == drawn_card_id)
                )
                card_name = name_result.scalar_one_or_none() or drawn_card_id
                default_label = f"Turn {turn_number}: drew {card_name}"
            else:
                default_label = f"Turn {turn_number} (empty library)"
            label = node_in.label or default_label
        else:
            all_card_ids = {
                *parent_state.library,
                *parent_state.hand,
                *parent_state.battlefield,
                *parent_state.graveyard,
                *parent_state.exile,
                *(
                    {
                        *parent_state.opponent_zones.library,
                        *parent_state.opponent_zones.hand,
                        *parent_state.opponent_zones.battlefield,
                        *parent_state.opponent_zones.graveyard,
                        *parent_state.opponent_zones.exile,
                    }
                    if parent_state.opponent_zones
                    else set()
                ),
            }
            card_names: dict[str, str] = {}
            if all_card_ids:
                names_result = await db.execute(
                    select(Card.id, Card.name).where(Card.id.in_(all_card_ids))
                )
                card_names = dict(names_result.all())

            try:
                resulting_state, auto_label = apply_action(
                    parent_state, node_in.action, card_names
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            new_state = resulting_state.model_dump()
            label = node_in.label or auto_label
    elif parent_node and parent_node.state:
        # A freeform note under a 3b node carries the state forward unchanged
        # — nothing happened to the game, so nothing should be lost.
        new_state = parent_node.state

    if not label:
        raise HTTPException(status_code=400, detail="label or action is required")

    siblings_result = await db.execute(
        select(GoldfishNode)
        .where(GoldfishNode.session_id == session_id)
        .where(GoldfishNode.parent_id == node_in.parent_id)
    )
    order_index = len(siblings_result.scalars().all())

    db_node = GoldfishNode(
        session_id=session_id,
        parent_id=node_in.parent_id,
        label=label,
        turn_number=turn_number,
        order_index=order_index,
        trackers=node_in.trackers or {},
        state=new_state,
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
