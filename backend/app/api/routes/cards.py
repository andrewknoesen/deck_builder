from fastapi import APIRouter

router = APIRouter()

@router.get("/search")
def search_cards(q: str):
    """
    Search for cards using Scryfall.
    """
    # Mock data for testing UI
    return {
        "data": [
            {
                "id": "mock-1",
                "name": "Black Lotus",
                "image_uris": {
                    "normal": "https://cards.scryfall.io/normal/front/b/d/bd8fa327-dd41-4737-8f19-2cf5eb1f7cdd.jpg?1614638838"
                }
            },
            {
                "id": "mock-2",
                "name": "Mox Pearl",
                "image_uris": {
                    "normal": "https://cards.scryfall.io/normal/front/e/d/ed0216a0-c5c9-4a99-b869-53e4d0256326.jpg?1614638847"
                }
            }
        ]
    }


@router.get("/{card_id}")
def get_card(card_id: str):
    """
    Get card by ID.
    """
    return {"message": f"Get card placeholder for: {card_id}"}
