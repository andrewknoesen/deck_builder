import httpx
from app.services.scryfall import ScryfallService, get_scryfall_service
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/search")
async def search_cards(
    q: str, scryfall: ScryfallService = Depends(get_scryfall_service)
):
    """
    Search for cards using Scryfall.
    """
    try:
        data = await scryfall.search_cards(q)
        return data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Scryfall error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{card_id}")
async def get_card(
    card_id: str, scryfall: ScryfallService = Depends(get_scryfall_service)
):
    """
    Get card by ID.
    """
    try:
        data = await scryfall.get_card_by_id(card_id)
        return data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Card not found")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Scryfall error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
