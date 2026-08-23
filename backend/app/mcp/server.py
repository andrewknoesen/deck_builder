"""MCP server exposing deck_builder's AI tool functions to external MCP clients.

Runs as a standalone stdio subprocess -- it never imports or boots the FastAPI
app (`app.main`). Each tool function already owns its own DB session / RAG
singleton / HTTP client, so this process only needs `app.core.config.settings`
(the same env-driven config every other one-off script in this repo uses).

Entry point (run from `backend/`):

    uv run python -m app.mcp.server

See `docs/mcp_server.md` for an example MCP client configuration.
"""

import logging
import sys
from contextlib import redirect_stdout

from mcp.server.fastmcp import FastMCP

# The stdio MCP transport requires stdout to carry *only* JSON-RPC frames.
# Importing the tool modules constructs the RAG singletons
# (app.ai.rag.cards.card_rag / rules_rag), which print status messages
# (embedding model load, ChromaDB connection) straight to stdout on import --
# redirect stdout to stderr for the duration of these imports so that noise
# can't corrupt the protocol stream before the server even starts running.
with redirect_stdout(sys.stderr):
    from app.ai.tools.cards import search_cards, search_cards_semantic
    from app.ai.tools.rules import lookup_glossary_term, query_comprehensive_rules
    from app.ai.tools.scryfall import lookup_card_rulings

# The shared "app" logger (app.core.logging) also writes to stdout by
# default -- fine for the FastAPI process, but every tool-call log line
# would otherwise land in the same stream as JSON-RPC frames here. Point its
# handler(s) at stderr instead, in-process only -- doesn't touch the shared
# logging setup the FastAPI app relies on.
for _handler in logging.getLogger("app").handlers:
    _handler.stream = sys.stderr

mcp = FastMCP("deck_builder")

mcp.add_tool(search_cards)
mcp.add_tool(search_cards_semantic)
mcp.add_tool(query_comprehensive_rules)
mcp.add_tool(lookup_glossary_term)
mcp.add_tool(lookup_card_rulings)

if __name__ == "__main__":
    mcp.run(transport="stdio")
