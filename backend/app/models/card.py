from typing import Dict, List, Optional
from sqlmodel import Field, SQLModel, Column, JSON

class CardBase(SQLModel):
    id: str = Field(primary_key=True)
    name: str
    mana_cost: Optional[str] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    colors: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    image_uris: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))

class Card(CardBase, table=True):
    pass
