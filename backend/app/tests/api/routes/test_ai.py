from app.core.config import settings
from fastapi.testclient import TestClient


def test_ai_suggest(client: TestClient) -> None:
    data = {"deck_context": ["Black Lotus"], "query": "Suggest something expensive"}
    response = client.post(f"{settings.API_V1_STR}/ai/suggest", json=data)
    assert response.status_code == 200
    assert "message" in response.json()

def test_ai_chat(client: TestClient) -> None:
    response = client.post(f"{settings.API_V1_STR}/ai/chat")
    assert response.status_code == 200
    assert response.json() == {"message": "AI chat placeholder"}
