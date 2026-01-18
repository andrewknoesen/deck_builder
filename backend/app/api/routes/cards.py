from fastapi import APIRouter

router = APIRouter()

@router.get("/search")
def search_cards(q: str):
    """
    Search for cards using Scryfall.
    """
    return {"message": f"Search placeholder for: {q}"}

@router.get("/{card_id}")
def get_card(card_id: str):
    """
    Get card by ID.
    """
    return {"message": f"Get card placeholder for: {card_id}"}
