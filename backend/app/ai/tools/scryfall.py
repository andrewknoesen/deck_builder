from typing import List

from app.core.logging import logger


def lookup_card_rulings(card_names: List[str]) -> str:
    """
    Fetches official rulings for the given cards from Scryfall.
    Returns a formatted string of rulings.
    """
    # This is a placeholder that would ideally use a dedicated get_rulings service.
    # Since existing architecture only showed 'search_cards', we might need to expand app/services/scryfall.py
    # or implement a direct call here. For Phase 1 demo, we'll mock or implement simple logic.

    # Real implementation needs to hit https://api.scryfall.com/cards/named?exact=...&format=json, then /rulings
    # For now, let's return a stub if service isn't ready, or try to use search_cards.

    results = []
    logger.info(f"Tool 'lookup_card_rulings' called with: {card_names}")
    for name in card_names:
        # TODO: Implement actual Ruling fetch.
        # For now, we simulate finding the card.
        results.append(
            f"Card: {name}\nNo rulings found (active Scryfall rulings fetch not yet implemented)."
        )

    return "\n\n".join(results)
