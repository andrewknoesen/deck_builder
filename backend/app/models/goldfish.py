from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


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


class GoldfishNode(GoldfishNodeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow_naive)


class GoldfishNodeCreate(SQLModel):
    parent_id: Optional[int] = None
    label: str
    turn_number: Optional[int] = None


class GoldfishNodePublic(GoldfishNodeBase):
    id: int
    created_at: datetime
