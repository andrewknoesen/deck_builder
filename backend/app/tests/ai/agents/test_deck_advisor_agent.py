from app.ai.agents.deck_advisor.deck_advisor_agent import PROMPT, deck_advisor_agent
from app.ai.tools.cards import search_cards, search_cards_semantic


def test_deck_advisor_agent_registers_both_search_tools() -> None:
    # Phase 5 added search_cards_semantic alongside the original search_cards
    # -- the agent should combine both, not swap one for the other.
    assert deck_advisor_agent.tools == [search_cards, search_cards_semantic]


def test_prompt_instructs_verifying_semantic_hits_before_citing() -> None:
    assert "search_cards_semantic" in PROMPT
    assert "verify" in PROMPT.lower()
