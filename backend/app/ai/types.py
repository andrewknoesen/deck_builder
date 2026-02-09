from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
