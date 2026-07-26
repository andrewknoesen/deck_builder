from typing import Callable, List

from google.adk.agents import Agent

from app.core.config import settings


def make_agent(
    *, name: str, description: str, instruction: str, tools: List[Callable]
) -> Agent:
    """
    Thin factory for this codebase's ADK Agent instances: Gemini model from
    settings plus plain-function tools, nothing else. Extracted once a
    second agent (deck_advisor_agent) duplicated rules_agent's boilerplate —
    see PLAN.md's Phase 0 decision log for why this waited until now.
    """
    return Agent(
        name=name,
        model=settings.AI_MODEL_NAME,
        description=description,
        instruction=instruction,
        tools=tools,
    )
