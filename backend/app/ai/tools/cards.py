from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services.scryfall import ScryfallService


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
    Searches Scryfall for cards matching a query (Scryfall search syntax).
    Returns formatted results: name, mana cost, type line, oracle text, and
    — if a format is given — that format's legality, so the agent can filter
    candidates itself instead of relying on internal memory for card details.
    """
    logger.info(f"Tool 'search_cards' called with query={query!r} format={format!r}")

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
