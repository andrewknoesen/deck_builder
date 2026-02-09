from typing import Any, Dict, List, Optional

import pytest
from app.ai.ingestion.base import (
    ContentSplitter,
    EmbeddingModel,
    IngestionDocument,
    IngestionSource,
    PipelineContext,
    ProcessedChunk,
    SectionParser,
    VectorStore,
)

# --- Mock Implementations for ABCs ---


class MockSource(IngestionSource):
    def load(self, context: PipelineContext) -> IngestionDocument:
        return IngestionDocument(content="test content", source_id="test_source")


class MockSplitter(ContentSplitter):
    def split(
        self, document: IngestionDocument, context: PipelineContext
    ) -> List[IngestionDocument]:
        return [document]


class MockParser(SectionParser):
    def parse(
        self, section: IngestionDocument, context: PipelineContext
    ) -> List[ProcessedChunk]:
        return [ProcessedChunk(id="1", text=section.content)]


class MockEmbedder(EmbeddingModel):
    def embed(
        self, chunks: List[ProcessedChunk], context: PipelineContext
    ) -> List[ProcessedChunk]:
        for chunk in chunks:
            chunk.embedding = [0.1, 0.2, 0.3]
        return chunks


class MockVectorStore(VectorStore):
    def upsert(self, chunks: List[ProcessedChunk], context: PipelineContext) -> None:
        pass

    def search(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[ProcessedChunk]:
        return []

    def delete(self, ids: List[str], context: PipelineContext) -> None:
        pass


# --- Tests ---


def test_pipeline_context_creation():
    context = PipelineContext(execution_id="123", timestamp=100.0)
    assert context.execution_id == "123"
    assert context.timestamp == 100.0
    assert context.config == {}


def test_ingestion_document_creation():
    doc = IngestionDocument(content="hello", source_id="src1", metadata={"key": "val"})
    assert doc.content == "hello"
    assert doc.source_id == "src1"
    assert doc.metadata["key"] == "val"


def test_processed_chunk_creation():
    chunk = ProcessedChunk(id="chk1", text="chunk text")
    assert chunk.id == "chk1"
    assert chunk.text == "chunk text"
    assert chunk.embedding is None


def test_mock_implementations():
    context = PipelineContext(execution_id="test", timestamp=0.0)

    # Source
    source = MockSource()
    doc = source.load(context)
    assert isinstance(doc, IngestionDocument)

    # Splitter
    splitter = MockSplitter()
    docs = splitter.split(doc, context)
    assert len(docs) == 1

    # Parser
    parser = MockParser()
    chunks = parser.parse(docs[0], context)
    assert len(chunks) == 1
    assert chunks[0].text == "test content"

    # Embedder
    embedder = MockEmbedder()
    embedded_chunks = embedder.embed(chunks, context)
    assert embedded_chunks[0].embedding == [0.1, 0.2, 0.3]

    # Vector Store
    store = MockVectorStore()
    store.upsert(embedded_chunks, context)
    results = store.search("query")
    assert results == []


def test_abc_enforcement():
    # Ensure standard ABC behavior: cannot instantiate without implementing abstract methods
    class IncompleteSource(IngestionSource):
        pass

    with pytest.raises(TypeError):
        IncompleteSource()
