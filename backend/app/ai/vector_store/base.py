from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.ai.types import PipelineContext, ProcessedChunk


class EmbeddingModel(ABC):
    """Abstract base class for embedding text chunks."""

    @abstractmethod
    def embed(
        self, chunks: List[ProcessedChunk], context: PipelineContext
    ) -> List[ProcessedChunk]:
        """Generates embeddings for a list of chunks and returns them (modified in-place or new list)."""
        pass


class VectorStore(ABC):
    """Abstract base class for vector database operations."""

    @abstractmethod
    def upsert(self, chunks: List[ProcessedChunk], context: PipelineContext) -> None:
        """Inserts or updates chunks in the vector store."""
        pass

    @abstractmethod
    def search(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[ProcessedChunk]:
        """Searches for chunks semantically similar to the query."""
        pass

    @abstractmethod
    def delete(self, ids: List[str], context: PipelineContext) -> None:
        """Deletes chunks by their IDs."""
        pass
