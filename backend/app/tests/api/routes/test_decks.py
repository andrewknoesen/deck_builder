from app.core.config import settings
from fastapi.testclient import TestClient


def test_read_decks(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/decks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_deck(client: TestClient) -> None:
    response = client.post(f"{settings.API_V1_STR}/decks/")
    assert response.status_code == 200
    assert response.json() == {"message": "Create deck placeholder"}

def test_get_deck_by_id(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/decks/1")
    assert response.status_code == 200
    assert response.json() == {"message": "Get deck placeholder for: 1"}
