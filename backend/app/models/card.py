from typing import Any, Dict, List, Optional
from sqlmodel import Field, SQLModel, Column, JSON

class CardBase(SQLModel):
    id: str = Field(primary_key=True)
    name: str
    mana_cost: Optional[str] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    colors: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    produced_mana: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    image_uris: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    legalities: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    # Raw Scryfall `card_faces` array, verbatim, for double-faced/split/adventure
    # cards -- each face has its own name/mana_cost/type_line/oracle_text/
    # image_uris. Only the front face's data is mirrored into the flat fields
    # above (see resolve_card_fields in app/services/scryfall.py); this is
    # what lets the UI show the back face too.
    card_faces: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))

class Card(CardBase, table=True):
    pass
