from app.ai.agents.rules.rules_agent import rules_agent
from app.schemas.ai import ChatRequest, ChatResponse
from fastapi import APIRouter

from typing import List

from pydantic import BaseModel
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


@router.post("/chat", response_model=ChatResponse)
async def chat_assistant(request: ChatRequest):
    """
    Chat with the Rules Agent.
    """
    response = await rules_agent.chat(request.message, request.context_cards)
    return ChatResponse(response=response)
