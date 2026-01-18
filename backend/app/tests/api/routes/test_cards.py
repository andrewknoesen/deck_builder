from app.core.config import settings
from fastapi.testclient import TestClient


def test_search_cards(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/cards/search?q=lotus")
    assert response.status_code == 200
    content = response.json()
    assert "data" in content
    assert len(content["data"]) > 0
    assert content["data"][0]["name"] == "Black Lotus"

def test_get_card_by_id(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/cards/123")
    assert response.status_code == 200
    assert response.json() == {"message": "Get card placeholder for: 123"}
