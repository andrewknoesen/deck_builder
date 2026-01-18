from typing import Any, Dict, List

import httpx

from app.core.config import settings


class ScryfallService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def search_cards(self, query: str) -> Dict[str, Any]:
        params = {"q": query}
        response = await self.client.get("/cards/search", params=params)
        response.raise_for_status()
        return response.json()

    async def get_card_by_id(self, card_id: str) -> Dict[str, Any]:
        response = await self.client.get(f"/cards/{card_id}")
        response.raise_for_status()
        return response.json()

    async def get_cards_by_ids(self, card_ids: List[str]) -> List[Dict[str, Any]]:
        # Scryfall collection API takes up to 75 IDs
        # For now we'll assume the deck isn't massive or we'd need to chunk
        identifiers = [{"id": cid} for cid in card_ids]
        response = await self.client.post("/cards/collection", json={"identifiers": identifiers})
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

async def get_scryfall_service():
    async with httpx.AsyncClient(base_url=settings.SCRYFALL_BASE_URL, timeout=30.0) as client:
        yield ScryfallService(client)
