import re
from typing import Optional

import httpx
from sqlmodel import col, select

from app.ai.rag.cards import card_rag
from app.ai.tools.db import get_tool_session
from app.core.config import settings
from app.core.logging import logger
from app.models.card import Card
from app.services.scryfall import ScryfallService

# Scryfall search syntax uses "key:value" operators (t:creature, c:red,
# f:pauper, ...). The local cache only supports plain name substring
# matching, not that grammar, so anything using an operator skips the local
# lookup and goes straight to live Scryfall to keep results correct.
_SCRYFALL_OPERATOR_RE = re.compile(r"\b[a-zA-Z]+:")


def _card_to_dict(card: Card) -> dict:
    return {
        "name": card.name,
        "mana_cost": card.mana_cost,
        "type_line": card.type_line,
        "oracle_text": card.oracle_text,
        "legalities": card.legalities,
    }


async def _search_local(query: str, limit: int = 10) -> list[dict]:
    async with get_tool_session() as session:
        result = await session.execute(
            select(Card).where(col(Card.name).ilike(f"%{query}%")).limit(limit)
        )
        return [_card_to_dict(card) for card in result.scalars().all()]


def _format_card(card: dict, format: Optional[str]) -> str:
    name = card.get("name", "Unknown")
    mana_cost = card.get("mana_cost", "")
    type_line = card.get("type_line", "")
    oracle_text = (card.get("oracle_text") or "").strip()

    lines = [f"{name} {mana_cost} — {type_line}".strip()]
    if oracle_text:
        lines.append(oracle_text)
    if format:
        legality = (card.get("legalities") or {}).get(format, "not_legal")
        lines.append(f"Legality ({format}): {legality}")

    return "\n".join(lines)


async def search_cards(query: str, format: Optional[str] = None) -> str:
    """
    Searches for cards matching a query (Scryfall search syntax). Plain name
    queries check the locally-ingested card cache first, falling back to live
    Scryfall if nothing matches there or the query uses Scryfall's operator
    syntax (t:, c:, f:, ...). Returns formatted results: name, mana cost,
    type line, oracle text, and — if a format is given — that format's
    legality, so the agent can filter candidates itself instead of relying on
    internal memory for card details.
    """
    logger.info(f"Tool 'search_cards' called with query={query!r} format={format!r}")

    if not _SCRYFALL_OPERATOR_RE.search(query):
        local_cards = await _search_local(query)
        if local_cards:
            return "\n\n".join(_format_card(card, format) for card in local_cards)

    async with httpx.AsyncClient(
        base_url=settings.SCRYFALL_BASE_URL, timeout=10.0
    ) as client:
        service = ScryfallService(client)
        try:
            result = await service.search_cards(query)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"No cards found for query: {query}"
            logger.error(f"HTTP error searching cards for {query!r}: {e}")
            return f"Error searching cards: {e}"

    cards = result.get("data", [])
    if not cards:
        return f"No cards found for query: {query}"

    formatted = [_format_card(card, format) for card in cards[:10]]
    return "\n\n".join(formatted)


def _doc_to_card(doc: str) -> dict:
    """Splits a card_rag document ('name\\ntype_line\\noracle_text') back
    into the dict shape _format_card expects. No mana_cost/legalities --
    those aren't part of the embedded text (see search_cards_semantic)."""
    name, _, rest = doc.partition("\n")
    type_line, _, oracle_text = rest.partition("\n")
    return {"name": name, "type_line": type_line, "oracle_text": oracle_text}


async def search_cards_semantic(query: str, k: int = 10) -> str:
    """
    Finds cards by what they DO semantically -- synergy, mechanics, effects
    -- rather than by exact oracle-text wording. Use this instead of
    'search_cards' for synergy/mechanic-style questions where the exact
    phrase isn't expected to appear verbatim in a matching card's oracle
    text (e.g. "cards that benefit when an artifact leaves the
    battlefield", "cards that deal damage when an artifact enters the
    battlefield"). Results do NOT include legality or mana cost -- before
    citing or recommending any card found here, verify its exact name, mana
    cost, and format legality via 'search_cards' (passing the deck's
    format), the same way any other new candidate must be verified.
    """
    logger.info(f"Tool 'search_cards_semantic' called with query={query!r} k={k}")

    docs = card_rag.query(query, k=k)
    if not docs:
        return f"No cards found for query: {query}"

    formatted = [_format_card(_doc_to_card(doc), format=None) for doc in docs]
    return "\n\n".join(formatted)
