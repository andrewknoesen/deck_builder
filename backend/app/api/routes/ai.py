from fastapi import APIRouter, HTTPException
from app.ai.agents import rules_agent
from app.schemas.ai import ChatRequest, ChatResponse

router = APIRouter()

from pydantic import BaseModel
from typing import List

class SuggestCardRequest(BaseModel):
    deck_context: List[str]
    query: str

@router.post("/suggest")
def suggest_cards(request: SuggestCardRequest):
    """
    Get card suggestions based on deck context and user query.
    """
    return {"message": "AI suggestion placeholder", "query": request.query}


@router.post("/chat", response_model=ChatResponse)
async def chat_assistant(request: ChatRequest):
    """
    Chat with the Rules Agent.
    """
    response = await rules_agent.chat(request.message, request.context_cards)
    return ChatResponse(response=response)

