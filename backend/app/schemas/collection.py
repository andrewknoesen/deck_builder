from typing import Optional
from pydantic import BaseModel
from app.models.deck import ScryfallCardPublic

class CollectionCardCreate(BaseModel):
    card_id: str
    quantity: int = 1

class CollectionCardUpdate(BaseModel):
    quantity: int

class CollectionCardRead(BaseModel):
    id: int
    card_id: str
    quantity: int
    card: Optional[ScryfallCardPublic] = None
