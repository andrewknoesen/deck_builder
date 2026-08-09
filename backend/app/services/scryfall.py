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
        response = await self.client.post(
            "/cards/collection", json={"identifiers": identifiers}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    async def get_collection(self, identifiers: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Batch lookup by arbitrary identifiers (name, or set+collector_number).
        Scryfall accepts up to 75 identifiers per request and returns
        {"data": [...found cards...], "not_found": [...unmatched identifiers...]}.
        """
        response = await self.client.post(
            "/cards/collection", json={"identifiers": identifiers}
        )
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


def resolve_card_fields(card_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Multi-faced cards (transform, modal DFC, reversible, art series, ...) don't
    always populate top-level `image_uris` — Scryfall puts per-face images
    under `card_faces` instead, and every caller that builds a local `Card`
    row has to fall back to the front face for it.

    Confirmed against the live API for two distinct cases before writing this
    (not guessed):
    - Ordinary transform/modal-DFC cards (e.g. "Delver of Secrets //
      Insectile Aberration", "Bala Ged Recovery // Bala Ged Sanctuary"): the
      top-level `name`/`type_line` are genuinely the correct combined "Front
      // Back" form — only `image_uris` is missing and needs the fallback.
    - Reversible alternate-frame prints (`layout: "reversible_card"`) and
      art-only prints (`layout: "art_series"`), where both faces are
      literally the same card: Scryfall's own top-level `name`/`type_line`
      are already a degenerate doubled/placeholder form (e.g. "Command Tower
      // Command Tower", "Card // Card", or missing entirely). For these the
      front face's own `name`/`type_line` is what should actually display.

    Detected structurally — both faces sharing the same `name` — rather than
    hardcoding a layout string list, so this doesn't silently miss a future
    Scryfall layout with the same "both faces are the same card" shape.
    """
    faces = card_data.get("card_faces") or []
    name = card_data.get("name", "")
    type_line = card_data.get("type_line")
    image_uris = card_data.get("image_uris")

    if faces:
        if image_uris is None:
            image_uris = faces[0].get("image_uris")

        face_names = [face.get("name") for face in faces]
        if len(face_names) >= 2 and face_names[0] and face_names[0] == face_names[1]:
            name = face_names[0]
            type_line = faces[0].get("type_line") or type_line

    return {
        "name": name,
        "type_line": type_line,
        "image_uris": image_uris,
        # Raw, unfiltered -- lets the frontend show the back face (name,
        # mana_cost, type_line, oracle_text, image_uris are all per-face on
        # Scryfall's side for these layouts). None rather than [] when there
        # aren't multiple faces, so callers can treat it as "nothing to flip
        # to" with a plain truthiness check.
        "card_faces": faces or None,
    }
