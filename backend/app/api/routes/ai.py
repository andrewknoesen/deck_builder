from typing import List

from app.ai.agents.rules.rules_agent import rules_agent
from app.schemas.ai import ChatRequest, ChatResponse
from fastapi import APIRouter
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types
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
    runner = InMemoryRunner(agent=rules_agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="api-user"
    )
    message = genai_types.Content(
        role="user", parts=[genai_types.Part(text=request.message)]
    )

    final_text = ""
    async for event in runner.run_async(
        user_id=session.user_id, session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or ""

    return ChatResponse(response=final_text)
