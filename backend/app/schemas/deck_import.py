from typing import List, Optional

from pydantic import BaseModel


class DeckImportRequest(BaseModel):
    text: str
    name: Optional[str] = None


class DeckImportResponse(BaseModel):
    id: int
    title: str
    missing_cards: List[str]
