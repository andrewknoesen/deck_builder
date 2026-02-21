from abc import ABC, abstractmethod
from typing import List


class RAGService(ABC):
    """Abstract base class for RAG (Retrieval-Augmented Generation) services."""

    @abstractmethod
    def query(self, text: str, k: int = 5) -> List[str]:
        """Retrieves relevant text chunks for a given query."""
        pass
