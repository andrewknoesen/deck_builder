from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class SuggestCardRequest(BaseModel):
    deck_context: List[str]
    query: str

@router.post("/suggest")
def suggest_cards(request: SuggestCardRequest):
    """
    Get card suggestions based on deck context and user query.
    """
    return {"message": "AI suggestion placeholder", "query": request.query}

@router.post("/chat")
def chat_assistant():
    """
    Simple chat interface for deck building advice.
    """
    return {"message": "AI chat placeholder"}
