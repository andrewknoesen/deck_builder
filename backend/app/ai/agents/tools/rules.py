from app.ai.agents.core.base import BaseTool
from app.ai.rag.rules import rules_rag
from app.core.logging import logger


class RulesTool(BaseTool):
    """Base for tools that RulesAgent can use."""

    pass


class LookupComprehensiveRulesFromQuery(RulesTool):
    """
    Searches the Magic: The Gathering Comprehensive Rules for relevant sections.
    """

    @property
    def name(self) -> str:
        return "lookup_comprehensive_rules"

    def run(self, query: str, **kwargs) -> str:
        logger.info(f"Tool 'query_comprehensive_rules' called with query: '{query}'")

        docs = rules_rag.query(query, k=5)
        if not docs:
            return "No relevant rules found in the Comprehensive Rules."

        return "\n\n".join([f"--- Rule Excerpt ---\n{doc}" for doc in docs])


class ExplainStackInteraction(RulesTool):
    """
    Looks up a term in the Magic: The Gathering Glossary.
    """

    @property
    def name(self) -> str:
        return "explain_stack_interaction"

    def run(self, term: str) -> str:
        logger.info(f"Tool 'lookup_glossary_term' called with term: '{term}'")
        docs = rules_rag.query_glossary(term, k=3)
        if not docs:
            return f"No glossary entry found for '{term}'."

        return "\n\n".join([f"--- Glossary Entry ---\n{doc}" for doc in docs])
