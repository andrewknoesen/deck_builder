from unittest.mock import AsyncMock, patch

import pytest
from app.ai.tools.cards import search_cards
from app.services.scryfall import ScryfallService


@pytest.mark.asyncio
async def test_search_cards_formats_results_with_legality() -> None:
    mock_response = {
        "data": [
            {
                "name": "Lightning Bolt",
                "mana_cost": "{R}",
                "type_line": "Instant",
                "oracle_text": "Lightning Bolt deals 3 damage to any target.",
                "legalities": {"modern": "legal", "standard": "not_legal"},
            }
        ]
    }
    with patch.object(
        ScryfallService, "search_cards", new=AsyncMock(return_value=mock_response)
    ):
        result = await search_cards("bolt", format="modern")

    assert "Lightning Bolt" in result
    assert "3 damage" in result
    assert "Legality (modern): legal" in result


@pytest.mark.asyncio
async def test_search_cards_no_results() -> None:
    with patch.object(
        ScryfallService, "search_cards", new=AsyncMock(return_value={"data": []})
    ):
        result = await search_cards("nonexistent-card-xyz")

    assert "No cards found" in result


@pytest.mark.asyncio
async def test_search_cards_without_format_omits_legality() -> None:
    mock_response = {
        "data": [
            {
                "name": "Sol Ring",
                "mana_cost": "{1}",
                "type_line": "Artifact",
                "oracle_text": "Add {2}.",
                "legalities": {"commander": "legal"},
            }
        ]
    }
    with patch.object(
        ScryfallService, "search_cards", new=AsyncMock(return_value=mock_response)
    ):
        result = await search_cards("sol ring")

    assert "Sol Ring" in result
    assert "Legality" not in result
