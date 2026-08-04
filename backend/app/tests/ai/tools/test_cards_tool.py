from unittest.mock import AsyncMock, patch

import pytest
from app.ai.tools import cards as cards_module
from app.ai.tools.cards import search_cards
from app.models.card import Card
from app.services.scryfall import ScryfallService
from sqlalchemy.ext.asyncio import AsyncSession


class _SessionCtx:
    """Wraps an already-open test AsyncSession as an async context manager,
    matching get_tool_session()'s real return shape."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def __aenter__(self) -> AsyncSession:
        return self._session

    async def __aexit__(self, *exc: object) -> bool:
        return False


@pytest.mark.asyncio
async def test_search_cards_formats_results_with_legality(db_session) -> None:
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
        cards_module, "get_tool_session", lambda: _SessionCtx(db_session)
    ):
        with patch.object(
            ScryfallService, "search_cards", new=AsyncMock(return_value=mock_response)
        ):
            result = await search_cards("bolt", format="modern")

    assert "Lightning Bolt" in result
    assert "3 damage" in result
    assert "Legality (modern): legal" in result


@pytest.mark.asyncio
async def test_search_cards_no_results(db_session) -> None:
    with patch.object(
        cards_module, "get_tool_session", lambda: _SessionCtx(db_session)
    ):
        with patch.object(
            ScryfallService, "search_cards", new=AsyncMock(return_value={"data": []})
        ):
            result = await search_cards("nonexistent-card-xyz")

    assert "No cards found" in result


@pytest.mark.asyncio
async def test_search_cards_without_format_omits_legality(db_session) -> None:
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
        cards_module, "get_tool_session", lambda: _SessionCtx(db_session)
    ):
        with patch.object(
            ScryfallService, "search_cards", new=AsyncMock(return_value=mock_response)
        ):
            result = await search_cards("sol ring")

    assert "Sol Ring" in result
    assert "Legality" not in result


@pytest.mark.asyncio
async def test_search_cards_hits_local_cache_before_scryfall(db_session) -> None:
    db_session.add(
        Card(
            id="lightning-bolt",
            name="Lightning Bolt",
            mana_cost="{R}",
            type_line="Instant",
            oracle_text="Lightning Bolt deals 3 damage to any target.",
            legalities={"modern": "legal"},
        )
    )
    await db_session.commit()

    with patch.object(
        cards_module, "get_tool_session", lambda: _SessionCtx(db_session)
    ):
        with patch.object(
            ScryfallService,
            "search_cards",
            new=AsyncMock(side_effect=AssertionError("should not hit Scryfall")),
        ):
            result = await search_cards("bolt", format="modern")

    assert "Lightning Bolt" in result
    assert "Legality (modern): legal" in result


@pytest.mark.asyncio
async def test_search_cards_falls_back_to_scryfall_when_local_cache_misses(
    db_session,
) -> None:
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
        cards_module, "get_tool_session", lambda: _SessionCtx(db_session)
    ):
        with patch.object(
            ScryfallService, "search_cards", new=AsyncMock(return_value=mock_response)
        ):
            result = await search_cards("sol ring")

    assert "Sol Ring" in result


@pytest.mark.asyncio
async def test_search_cards_with_operator_syntax_skips_local_cache(db_session) -> None:
    db_session.add(
        Card(id="lightning-bolt", name="Lightning Bolt", legalities={"modern": "legal"})
    )
    await db_session.commit()

    mock_response = {"data": [{"name": "Some Red Creature", "type_line": "Creature"}]}
    with patch.object(
        cards_module, "get_tool_session", lambda: _SessionCtx(db_session)
    ):
        with patch.object(
            ScryfallService, "search_cards", new=AsyncMock(return_value=mock_response)
        ) as mock_search:
            result = await search_cards("t:creature c:red")

    mock_search.assert_awaited_once()
    assert "Some Red Creature" in result
