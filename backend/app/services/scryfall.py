from app.core.logging import setup_logging
from typing import Any, Dict, List

import httpx
from fastapi import Request

from app.core.config import settings

logger = setup_logging()

# Card data by ID is immutable (a given Scryfall printing never changes), so
# it's safe to cache for the life of the process. Unbounded is fine here:
# the working set is whatever small number of specific cards the app looks
# up by ID (e.g. the landing page's hero card, hit on every visit) rather
# than the full ~90k-card catalog.
_card_by_id_cache: Dict[str, Dict[str, Any]] = {}


class ScryfallService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def search_cards(self, query: str) -> Dict[str, Any]:
        params = {"q": query}
        response = await self.client.get("/cards/search", params=params)
        response.raise_for_status()
        return response.json()

    async def get_card_by_id(self, card_id: str) -> Dict[str, Any]:
        if card_id in _card_by_id_cache:
            return _card_by_id_cache[card_id]
        response = await self.client.get(f"/cards/{card_id}")
        response.raise_for_status()
        data = response.json()
        _card_by_id_cache[card_id] = data
        return data

    async def get_cards_by_ids(self, card_ids: List[str]) -> List[Dict[str, Any]]:
        # Scryfall collection API takes up to 75 IDs
        # For now we'll assume the deck isn't massive or we'd need to chunk
        identifiers = [{"id": cid} for cid in card_ids]
        response = await self.client.post("/cards/collection", json={"identifiers": identifiers})
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    async def get_collection(self, identifiers: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Batch lookup by arbitrary identifiers (name, or set+collector_number).
        Scryfall accepts up to 75 identifiers per request and returns
        {"data": [...found cards...], "not_found": [...unmatched identifiers...]}.
        """
        response = await self.client.post("/cards/collection", json={"identifiers": identifiers})
        response.raise_for_status()
        return response.json()
    async def get_card_rulings(self, card_id: str) -> List[Dict[str, Any]]:
        response = await self.client.get(f"/cards/{card_id}/rulings")
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])



async def get_scryfall_service(request: Request) -> ScryfallService:
    # Reuses the single AsyncClient created once at app startup (see
    # app/main.py's lifespan) instead of opening a new connection per
    # request.
    return ScryfallService(request.app.state.scryfall_client)
