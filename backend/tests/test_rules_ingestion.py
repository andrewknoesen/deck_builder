from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.ai.ingestion.base import IngestionDocument
from app.ai.ingestion.rules_ingestion import (
    MtgGlossaryParser,
    MtgRuleParser,
    MtgRulesContentSplitter,
    WebSource,
)
from app.ai.types import PipelineContext, ProcessedChunk
from app.ai.vector_store.chroma import ChromaVectorStore
from app.ai.vector_store.embedding import SentenceTransformerEmbedder


@pytest.fixture
def mock_context():
    return PipelineContext(execution_id="test", timestamp=0.0)


# --- Test WebSource ---
@patch("aiohttp.ClientSession.get")
def test_web_source_load(mock_get, mock_context):
    # Setup mock response
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = "Rules Content"
    mock_get.return_value.__aenter__.return_value = mock_response

    source = WebSource("http://example.com")
    doc = source.load(mock_context)

    assert doc.content == "Rules Content"
    assert doc.source_id == "http://example.com"
    assert doc.metadata["source_type"] == "web"


# --- Test Splitter ---
def test_rules_splitter(mock_context):
    # Simulated content with markers
    content = """
Ignore this intro.
1. Game Concepts
Rule 100.
Glossary
Term 1
Credits
Made by WotC
"""
    doc = IngestionDocument(content=content, source_id="test")
    splitter = MtgRulesContentSplitter()
    parts = splitter.split(doc, mock_context)

    assert len(parts) == 2
    assert parts[0].metadata["section"] == "rules"
    assert "Rule 100." in parts[0].content
    assert parts[1].metadata["section"] == "glossary"
    assert "Term 1" in parts[1].content


# --- Test Rules Parser ---
def test_rule_parser(mock_context):
    content = """
100.1a This is a subrule.
100.2. Another rule with typo dot.
"""
    doc = IngestionDocument(
        content=content, source_id="test", metadata={"section": "rules"}
    )
    parser = MtgRuleParser()
    chunks = parser.parse(doc, mock_context)

    assert len(chunks) == 2
    assert chunks[0].metadata["rule_id"] == "100.1a"
    assert "This is a subrule." in chunks[0].text

    assert chunks[1].metadata["rule_id"] == "100.2"
    assert "Another rule" in chunks[1].text


# --- Test Glossary Parser ---
def test_glossary_parser(mock_context):
    content = """
Deathtouch
A static ability that kills stuff.

Flying
A static ability that avoids stuff.
"""
    doc = IngestionDocument(
        content=content, source_id="test", metadata={"section": "glossary"}
    )
    parser = MtgGlossaryParser()
    chunks = parser.parse(doc, mock_context)

    assert len(chunks) == 2
    assert chunks[0].metadata["term"] == "Deathtouch"
    assert chunks[0].id == "glossary_deathtouch"
    assert "kills stuff" in chunks[0].text

    assert chunks[1].metadata["term"] == "Flying"


# --- Test Embedder (Mocked) ---
@patch("app.ai.vector_store.embedding.SentenceTransformer")
def test_embedder(mock_st_class, mock_context):
    mock_model = MagicMock()
    # Return a dummy numpy-like object or list based on how implementation uses it
    # implementation: embeddings = self.model.encode(..., convert_to_numpy=True)
    # then: chunk.embedding = embeddings[i].tolist()

    # We need embeddings[i] to be an object that has a .tolist() method returning list[float]
    import numpy as np

    mock_model.encode.return_value = np.array([[0.1, 0.2]])
    mock_st_class.return_value = mock_model

    embedder = SentenceTransformerEmbedder(device="cpu")
    chunk = ProcessedChunk(id="1", text="hello")
    results = embedder.embed([chunk], mock_context)

    # Use approximate comparison for floats if needed, but exact matches for 0.1/0.2 should work here
    assert results[0].embedding == [0.1, 0.2]


# --- Test Vector Store (Mocked) ---
@patch("chromadb.HttpClient")
def test_vector_store_upsert(mock_http_client, mock_context):
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_http_client.return_value = mock_client

    store = ChromaVectorStore()
    chunk = ProcessedChunk(id="1", text="abc", embedding=[0.1, 0.2])

    store.upsert([chunk], mock_context)

    mock_collection.upsert.assert_called_once()
    call_args = mock_collection.upsert.call_args[1]
    assert call_args["ids"] == ["1"]
    assert call_args["embeddings"] == [[0.1, 0.2]]


# --- Test Vector Store Search ---
@patch("chromadb.HttpClient")
def test_vector_store_search(mock_http_client, mock_context):
    # Setup mocks
    mock_client_instance = MagicMock()
    mock_collection = MagicMock()
    mock_client_instance.get_or_create_collection.return_value = mock_collection
    mock_http_client.return_value = mock_client_instance

    # Mock embedding model
    mock_embedder = MagicMock()

    def side_effect(chunks, context):
        for chunk in chunks:
            chunk.embedding = [0.1, 0.2, 0.3]
        return chunks

    mock_embedder.embed.side_effect = side_effect

    store = ChromaVectorStore(embedding_model=mock_embedder)
    
    # Setup search results
    # The return structure from collection.query
    mock_collection.query.return_value = {
        "ids": [["1"]],
        "documents": [["doc1"]],
        "metadatas": [[{"meta": "data"}]],
        "distances": [[0.1]],
    }

    results = store.search("query")

    assert len(results) == 1
    assert results[0].id == "1"
    assert results[0].text == "doc1"
    
    # Ensure query was called with correct embeddings
    mock_collection.query.assert_called_once()
    # args[0] are positional, args[1] are keyword
    call_args = mock_collection.query.call_args[1]
    
    # Check query_embeddings
    assert call_args["query_embeddings"] == [[0.1, 0.2, 0.3]]

