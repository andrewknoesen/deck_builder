from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class DeckCard(SQLModel, table=True):
    deck_id: Optional[int] = Field(default=None, foreign_key="deck.id", primary_key=True)
    card_id: str = Field(primary_key=True) # Scryfall ID
    quantity: int = 1
    board: str = "main" # main, side, commander

class Deck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    format: Optional[str] = None
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    cards: List[DeckCard] = Relationship()
