from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel
from sqlmodel import Column, Field, JSON, SQLModel, String


def _utcnow_naive() -> datetime:
    """Naive UTC datetime, matching the migration's TIMESTAMP WITHOUT TIME ZONE
    columns — asyncpg rejects a tz-aware value against a naive column."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


ZONES = ("library", "hand", "battlefield", "graveyard", "exile")


class Zones(BaseModel):
    """
    One player's zones — library/hand/battlefield/graveyard/exile as ordered
    card_id lists. Split out of `GameState` in Phase 3d so a second player's
    zones can be nested as `GameState.opponent_zones` without duplicating
    this shape.
    """

    library: List[str] = []
    hand: List[str] = []
    battlefield: List[str] = []
    graveyard: List[str] = []
    exile: List[str] = []

    def zone(self, name: str) -> List[str]:
        if name not in ZONES:
            raise ValueError(f"Unknown zone: {name}")
        return getattr(self, name)


class GameState(Zones):
    """
    A full snapshot of the goldfish game state at one node — the player's own
    zones (inherited flat from `Zones`, so every pre-3d stored state parses
    unchanged), plus life totals for both players and an optional second
    player's zones. Stored whole on every node (not a diff), same reasoning
    as `trackers`: reading a node's state should never require replaying
    history.
    """

    life_total: int = 20
    opponent_life_total: int = 20
    opponent_zones: Optional[Zones] = None
    # Phase 8 — running total mana value spent on `cast` actions, tracked
    # separately per side. Backend-computed (see `apply_action`'s `cast`
    # branch), not user-editable. Backfills to 0 for any pre-existing stored
    # node missing these keys, same JSON-column mechanism as every other
    # GameState field added since Phase 3b.
    mana_spent: int = 0
    opponent_mana_spent: int = 0


class GoldfishActionIn(BaseModel):
    type: Literal[
        "draw", "play_land", "cast", "move_zone", "set_life", "shuffle", "next_turn"
    ]
    card_id: Optional[str] = None
    from_zone: Optional[str] = None
    to_zone: Optional[str] = None
    life_total: Optional[int] = None
    target: Literal["self", "opponent"] = "self"


class GoldfishSessionBase(SQLModel):
    deck_id: int = Field(foreign_key="deck.id", index=True, ondelete="CASCADE")
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    opponent_deck_id: Optional[int] = Field(
        default=None, foreign_key="deck.id", index=True, ondelete="SET NULL"
    )
    # Manual, session-level, freely editable outcome (Phase 7) — not tied to
    # any specific tree branch/node, since a session's tree can have multiple
    # sibling lines with no server-side concept of "which one actually
    # happened." None means "not recorded." sa_column is explicit because
    # SQLModel can't auto-derive a column type from Optional[Literal[...]].
    outcome: Optional[Literal["win", "loss", "draw"]] = Field(
        default=None, sa_column=Column(String)
    )


class GoldfishSession(GoldfishSessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow_naive)


class GoldfishSessionCreate(SQLModel):
    deck_id: int
    name: Optional[str] = None
    opponent_deck_id: Optional[int] = None


class GoldfishSessionPublic(GoldfishSessionBase):
    id: int
    created_at: datetime


class GoldfishNodeBase(SQLModel):
    session_id: int = Field(
        foreign_key="goldfishsession.id", index=True, ondelete="CASCADE"
    )
    parent_id: Optional[int] = Field(
        default=None, foreign_key="goldfishnode.id", index=True
    )
    label: str
    turn_number: Optional[int] = None
    order_index: int = 0
    # Generic named-counter snapshot at this node (life totals, poison, storm
    # count, whatever the user is tracking) — an opaque key->value map, not a
    # fixed set of fields, so the frontend can add arbitrary trackers without
    # a schema change. Each node stores its own full snapshot (not a diff),
    # matching the state-snapshot approach PLAN.md's Phase 3b already commits
    # to for the same reason: simpler than replaying deltas up the tree.
    trackers: Optional[Dict[str, int]] = Field(default=None, sa_column=Column(JSON))
    # Phase 3b game-state snapshot (library/hand/battlefield/graveyard/exile +
    # life_total) — None for plain 3a free-text sessions/notes. Stored as a
    # plain dict column (not GameState directly) since SQLModel/SQLAlchemy
    # JSON columns hold JSON-serializable data, not pydantic model instances;
    # routes parse it into GameState via GameState(**node.state) to work with it.
    state: Optional[Dict] = Field(default=None, sa_column=Column(JSON))


class GoldfishNode(GoldfishNodeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow_naive)


class GoldfishNodeCreate(SQLModel):
    parent_id: Optional[int] = None
    label: Optional[str] = None
    turn_number: Optional[int] = None
    trackers: Optional[Dict[str, int]] = None
    action: Optional[GoldfishActionIn] = None


class GoldfishNodePublic(GoldfishNodeBase):
    id: int
    created_at: datetime
