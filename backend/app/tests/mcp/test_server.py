import pytest
from app.mcp.server import mcp

EXPECTED_TOOL_NAMES = {
    "search_cards",
    "search_cards_semantic",
    "query_comprehensive_rules",
    "lookup_glossary_term",
    "lookup_card_rulings",
}


@pytest.mark.asyncio
async def test_all_five_tools_registered() -> None:
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}

    assert names == EXPECTED_TOOL_NAMES
