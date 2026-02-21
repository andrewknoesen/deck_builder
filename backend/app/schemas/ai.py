from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    context_cards: Optional[List[str]] = []

class ChatResponse(BaseModel):
    response: str
