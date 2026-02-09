from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.ai.types import PipelineContext, ProcessedChunk


class IngestionDocument(BaseModel):
    """Represents a raw or partially processed document in the ingestion pipeline."""

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source_id: str


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
