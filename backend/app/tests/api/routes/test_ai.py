from types import SimpleNamespace
from unittest.mock import patch

import pytest
from app.core.config import settings
from google.adk.runners import InMemoryRunner
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_suggest(client: AsyncClient) -> None:
    data = {"deck_context": ["Black Lotus"], "query": "Suggest something expensive"}
    response = await client.post(f"{settings.API_V1_STR}/ai/suggest", json=data)
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_ai_chat(client: AsyncClient) -> None:
    async def fake_run_async(self, *, user_id, session_id, new_message, **kwargs):
        event = SimpleNamespace(
            content=SimpleNamespace(parts=[SimpleNamespace(text="[CR 702.1] Flying rules.")]),
            is_final_response=lambda: True,
        )
        yield event

    with patch.object(InMemoryRunner, "run_async", fake_run_async):
        response = await client.post(
            f"{settings.API_V1_STR}/ai/chat", json={"message": "What is flying?"}
        )

    assert response.status_code == 200
    assert response.json() == {"response": "[CR 702.1] Flying rules."}
