from typing import List, Literal, Optional

from app.models.goldfish import GoldfishNodePublic, GoldfishSessionPublic
from pydantic import BaseModel


class GoldfishSessionTree(BaseModel):
    session: GoldfishSessionPublic
    nodes: List[GoldfishNodePublic]


class GoldfishSessionOutcomeUpdate(BaseModel):
    outcome: Optional[Literal["win", "loss", "draw"]] = None


class GoldfishAnalyticsPublic(BaseModel):
    session_count: int
    sessions_with_outcome: int
    wins: int
    losses: int
    draws: int
    win_rate: Optional[float] = None  # None when sessions_with_outcome == 0
    average_max_turn: Optional[float] = None  # None when no node has turn_number set
    two_deck_session_ratio: Optional[float] = None  # None when session_count == 0
