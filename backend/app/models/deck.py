from typing import Dict, List, Optional

from sqlmodel import Field, Relationship, SQLModel

# --- DeckCard ---


class DeckCardBase(SQLModel):
    card_id: str = Field(primary_key=True)  # Scryfall ID
    quantity: int = 1
    board: str = "main"  # main, side, commander


class DeckCard(DeckCardBase, table=True):
    deck_id: Optional[int] = Field(
        default=None, foreign_key="deck.id", primary_key=True
    )

    deck: "Deck" = Relationship(back_populates="cards")


class DeckCardCreate(DeckCardBase):
    pass


# --- Deck ---


class DeckBase(SQLModel):
    title: str
    format: Optional[str] = None
    user_id: int = Field(foreign_key="user.id")


class Deck(DeckBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Relationships
    cards: List[DeckCard] = Relationship(
        back_populates="deck", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class DeckCreate(DeckBase):
    cards: Optional[List[DeckCardCreate]] = None


class DeckUpdate(SQLModel):
    title: Optional[str] = None
    format: Optional[str] = None
    cards: Optional[List[DeckCardCreate]] = None


class ScryfallCardPublic(SQLModel):
    id: str
    name: str
    mana_cost: Optional[str] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    colors: Optional[List[str]] = None
    image_uris: Optional[Dict[str, str]] = None


class DeckCardPublic(DeckCardBase):
    card: Optional[ScryfallCardPublic] = None


class DeckPublic(DeckBase):
    id: int
    cards: List[DeckCardPublic] = []
