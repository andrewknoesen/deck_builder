from unittest.mock import MagicMock, patch

from app.ai.types import PipelineContext, ProcessedChunk
from app.ai.vector_store.chroma import ChromaVectorStore


def test_upsert_skips_chunks_without_embeddings():
    with patch("app.ai.vector_store.chroma.chromadb.HttpClient") as mock_http_client:
        mock_collection = MagicMock()
        mock_http_client.return_value.get_or_create_collection.return_value = mock_collection

        store = ChromaVectorStore()
        chunks = [
            ProcessedChunk(id="a", text="has embedding", embedding=[0.1, 0.2]),
            ProcessedChunk(id="b", text="missing embedding", embedding=None),
            ProcessedChunk(id="c", text="also has embedding", embedding=[0.3, 0.4]),
        ]

        store.upsert(chunks, PipelineContext(execution_id="test", timestamp=0.0))

        _, kwargs = mock_collection.upsert.call_args
        assert kwargs["ids"] == ["a", "c"]
        assert len(kwargs["ids"]) == len(kwargs["embeddings"]) == len(kwargs["documents"]) == len(kwargs["metadatas"])
