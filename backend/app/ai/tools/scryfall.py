from typing import List

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.services.scryfall import ScryfallService



async def _fetch_rulings_for_card(service: ScryfallService, name: str) -> str:
    try:
        # 1. Search for the card exact match
        # Scryfall API raises 404 if not found
        search_result = await service.search_cards(f'!"{name}"')
        
        if not search_result.get("data"):
             return f"Card: {name}\nCard not found on Scryfall."
             
        card_data = search_result["data"][0]
        card_id = card_data.get("id")
        
        if not card_id:
             return f"Card: {name}\nCould not determine card ID."
             
        # 2. Fetch rulings
        definitions = await service.get_card_rulings(card_id)
        
        if not definitions:
            return f"Card: {name}\nNo rulings found."
            
        # 3. Format rulings
        ruling_texts = []
        for r in definitions:
            date = r.get("published_at", "")
            text = r.get("comment", "")
            ruling_texts.append(f"- [{date}] {text}")
        
        formatted_rulings = "\n".join(ruling_texts)
        return f"Card: {name}\n{formatted_rulings}"

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Card: {name}\nCard not found on Scryfall."
        logger.error(f"HTTP error fetching rulings for {name}: {e}")
        return f"Card: {name}\nError fetching rulings: {e}"
    except Exception as e:
        logger.error(f"Unexpected error fetching rulings for {name}: {e}")
        return f"Card: {name}\nError fetching rulings: {e}"


async def lookup_card_rulings(card_names: List[str]) -> str:
    """
    Fetches official rulings for the given cards from Scryfall.
    Returns a formatted string of rulings.
    """
    logger.info(f"Tool 'lookup_card_rulings' called with: {card_names}")
    results = []

    # Initialize service with async client
    async with httpx.AsyncClient(base_url=settings.SCRYFALL_BASE_URL, timeout=10.0) as client:
        service = ScryfallService(client)
        
        for name in card_names:
            result = await _fetch_rulings_for_card(service, name)
            results.append(result)

    return "\n\n".join(results)
