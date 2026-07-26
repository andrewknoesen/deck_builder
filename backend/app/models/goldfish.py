from datetime import datetime, timezone
from typing import Dict, Optional

from sqlmodel import Column, Field, JSON, SQLModel


def _utcnow_naive() -> datetime:
    """Naive UTC datetime, matching the migration's TIMESTAMP WITHOUT TIME ZONE
    columns — asyncpg rejects a tz-aware value against a naive column."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class GoldfishSessionBase(SQLModel):
    deck_id: int = Field(foreign_key="deck.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str


class GoldfishSession(GoldfishSessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow_naive)


class GoldfishSessionCreate(SQLModel):
    deck_id: int
    name: Optional[str] = None


class GoldfishSessionPublic(GoldfishSessionBase):
    id: int
    created_at: datetime


class GoldfishNodeBase(SQLModel):
    session_id: int = Field(foreign_key="goldfishsession.id", index=True)
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


class GoldfishNode(GoldfishNodeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow_naive)


class GoldfishNodeCreate(SQLModel):
    parent_id: Optional[int] = None
    label: str
    turn_number: Optional[int] = None
    trackers: Optional[Dict[str, int]] = None


class GoldfishNodePublic(GoldfishNodeBase):
    id: int
    created_at: datetime
