from app.models.goldfish import GoldfishNode, GoldfishSession
from app.schemas.goldfish import GoldfishAnalyticsPublic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select


async def compute_deck_analytics(
    db: AsyncSession, deck_id: int, user_id: int
) -> GoldfishAnalyticsPublic:
    """
    Aggregates every goldfishing session for a deck (owned by `user_id`,
    matching `list_sessions`'s `?deck_id=` + `user_id` scoping) into a single
    analytics summary. Deck-scoped only — no cross-deck rollup in v1.
    """
    sessions_result = await db.execute(
        select(GoldfishSession)
        .where(GoldfishSession.deck_id == deck_id)
        .where(GoldfishSession.user_id == user_id)
    )
    sessions = sessions_result.scalars().all()

    session_count = len(sessions)
    wins = sum(1 for s in sessions if s.outcome == "win")
    losses = sum(1 for s in sessions if s.outcome == "loss")
    draws = sum(1 for s in sessions if s.outcome == "draw")
    sessions_with_outcome = wins + losses + draws
    win_rate = wins / sessions_with_outcome if sessions_with_outcome else None

    two_deck_session_ratio = None
    if session_count:
        two_deck_sessions = sum(1 for s in sessions if s.opponent_deck_id is not None)
        two_deck_session_ratio = two_deck_sessions / session_count

    average_max_turn = None
    if sessions:
        session_ids = [s.id for s in sessions]
        nodes_result = await db.execute(
            select(GoldfishNode.session_id, GoldfishNode.turn_number).where(
                GoldfishNode.session_id.in_(session_ids)
            )
        )
        max_turn_by_session: dict[int, int] = {}
        for session_id, turn_number in nodes_result.all():
            if turn_number is None:
                continue
            current_max = max_turn_by_session.get(session_id)
            if current_max is None or turn_number > current_max:
                max_turn_by_session[session_id] = turn_number

        if max_turn_by_session:
            average_max_turn = sum(max_turn_by_session.values()) / len(
                max_turn_by_session
            )

    return GoldfishAnalyticsPublic(
        session_count=session_count,
        sessions_with_outcome=sessions_with_outcome,
        wins=wins,
        losses=losses,
        draws=draws,
        win_rate=win_rate,
        average_max_turn=average_max_turn,
        two_deck_session_ratio=two_deck_session_ratio,
    )
