from typing import Optional
from sqlmodel import Field, Relationship, SQLModel

from app.models.card import Card
from app.models.user import User

class CollectionCard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    card_id: str = Field(foreign_key="card.id", index=True)
    quantity: int = Field(default=1)

    # Relationships
    user: "User" = Relationship()
    card: "Card" = Relationship()
