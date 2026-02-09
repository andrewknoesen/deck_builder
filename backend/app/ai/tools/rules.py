# from app.ai.rag.rules import get_rules_rag
from app.ai.rag.rules import rules_rag
from app.core.logging import logger


def query_comprehensive_rules(query: str) -> str:
    """
    Searches the Magic: The Gathering Comprehensive Rules for relevant sections.
    """
    logger.info(f"Tool 'query_comprehensive_rules' called with query: '{query}'")
    # docs = get_rules_rag().query(query, k=5)
    docs = rules_rag.query(query, k=5)
    if not docs:
        return "No relevant rules found in the Comprehensive Rules."

    return "\n\n".join([f"--- Rule Excerpt ---\n{doc}" for doc in docs])


def lookup_glossary_term(term: str) -> str:
    """
    Looks up a term in the Magic: The Gathering Glossary.
    """
    logger.info(f"Tool 'lookup_glossary_term' called with term: '{term}'")
    docs = rules_rag.query_glossary(term, k=3)
    if not docs:
        return f"No glossary entry found for '{term}'."

    return "\n\n".join([f"--- Glossary Entry ---\n{doc}" for doc in docs])
