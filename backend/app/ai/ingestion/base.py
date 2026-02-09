from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestionDocument(BaseModel):
    """Represents a raw or partially processed document in the ingestion pipeline."""

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_id: str


class PipelineContext(BaseModel):
    """Context object to hold shared state/metadata throughout the pipeline execution."""

    execution_id: str
    timestamp: float
    config: Dict[str, Any] = Field(default_factory=dict)


class ProcessedChunk(BaseModel):
    """Represents a fully processed chunk of text ready for embedding/indexing."""

    id: str
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None

    # Optional fields for traceability
    source_document_id: Optional[str] = None
    start_char_idx: Optional[int] = None
    end_char_idx: Optional[int] = None


class IngestionSource(ABC):
    """Abstract base class for data sources (e.g., file, URL, database)."""

    @abstractmethod
    def load(self, context: PipelineContext) -> IngestionDocument:
        """Loads data from the source and returns an IngestionDocument."""
        pass


class ContentSplitter(ABC):
    """Abstract base class for splitting documents into major sections (e.g., Rules vs Glossary)."""

    @abstractmethod
    def split(
        self, document: IngestionDocument, context: PipelineContext
    ) -> List[IngestionDocument]:
        """Splits a single document into multiple logical sections."""
        pass


class SectionParser(ABC):
    """Abstract base class for parsing sections into granular chunks (e.g., individual rules)."""

    @abstractmethod
    def parse(
        self, section: IngestionDocument, context: PipelineContext
    ) -> List[ProcessedChunk]:
        """Parses a section document into a list of processed chunks."""
        pass


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
