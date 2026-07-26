from app.ai.agents.deck_advisor.deck_advisor_agent import deck_advisor_agent
from app.ai.agents.rules.rules_agent import rules_agent
from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.deck import Deck, DeckCard
from app.models.user import User
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    SuggestCardRequest,
    SuggestCardResponse,
)
from app.services.stats import calculate_stats
from fastapi import APIRouter, Depends, HTTPException
from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

router = APIRouter()


def _build_deck_context(deck: Deck, stats: dict, query: str) -> str:
    main_cards = [dc for dc in deck.cards if dc.board == "main" and dc.card]

    # Full details for every card already in the deck, straight from data this app
    # already synced from Scryfall (no extra query/network call) — this is what lets
    # the agent skip a search_cards round trip for cards it's already been given.
    fmt_key = (deck.format or "").lower()
    card_lines = []
    for dc in main_cards:
        card = dc.card
        line = f"{dc.quantity}x {card.name} {card.mana_cost or ''} — {card.type_line or ''}".strip()
        if fmt_key:
            legality = (card.legalities or {}).get(fmt_key, "unknown")
            line += f" [{deck.format} legality: {legality}]"
        card_lines.append(line)

    curve = stats.get("mana_curve", {})
    curve_line = ", ".join(f"{k}: {v}" for k, v in curve.items())

    color_stats = stats.get("color_stats") or {}
    color_lines = "\n".join(
        f"- {c}: {s['pips']} pips, {s['sources']} sources "
        f"(recommend {s['recommended_sources']})"
        for c, s in color_stats.items()
    )

    recs = stats.get("recommendations") or {}

    return f"""Deck: {deck.title}
Format: {deck.format or "Unknown"}

Current cards ({stats.get("total_cards", 0)} total):
{chr(10).join(card_lines) or "(empty)"}

Mana curve (by CMC): {curve_line}
Average CMC: {stats.get("average_cmc")}
Land count recommendation: {recs.get("land_count")} ({recs.get("reasoning")})

Color stats:
{color_lines or "(none)"}

User request: {query}"""


@router.post("/suggest", response_model=SuggestCardResponse)
async def suggest_cards(
    request: SuggestCardRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get card suggestions for a specific deck from the Deck Advisor agent.
    """
    result = await db.execute(
        select(Deck)
        .where(Deck.id == request.deck_id)
        .options(selectinload(Deck.cards).selectinload(DeckCard.card))  # type: ignore[arg-type]
    )
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    stats = calculate_stats(deck)
    context = _build_deck_context(deck, stats, request.query)

    runner = InMemoryRunner(agent=deck_advisor_agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="api-user"
    )
    message = genai_types.Content(role="user", parts=[genai_types.Part(text=context)])

    final_text = ""
    async for event in runner.run_async(
        user_id=session.user_id, session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or ""

    return SuggestCardResponse(response=final_text)


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
