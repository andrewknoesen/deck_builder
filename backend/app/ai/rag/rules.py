# from functools import lru_cache

from typing import List

from app.ai.rag.base import RAGService
from app.ai.types import ProcessedChunk
from app.ai.vector_store.chroma import ChromaVectorStore
from app.ai.vector_store.embedding import SentenceTransformerEmbedder


class RulesRAG(RAGService):
    """Retrieval-Augmented Generation for MTG Rules."""

    def __init__(self):
        self._enabled = False
        try:
            # We initialize the shared components.
            # In a real app, these might be injected or singletons managed by FastAPI dependencies.
            self.embedder = SentenceTransformerEmbedder()  # Will auto-detect device
            self.store = ChromaVectorStore(embedding_model=self.embedder)
            self._enabled = True
        except Exception as e:
            print(f"Failed to initialize RAG: {e}")
            self._enabled = False

    def query(self, text: str, k: int = 5) -> List[str]:
        """
        Retrieves top-k relevant rules for the query.
        Returns a list of rule texts.
        """
        if not self._enabled:
            return []

        try:
            chunks: List[ProcessedChunk] = self.store.search(text, limit=k)
            return [chunk.text for chunk in chunks]
        except Exception as e:
            print(f"RAG Query validation failed: {e}")
            return []


# @lru_cache()
# def get_rules_rag() -> RulesRAG:
#     return RulesRAG()

rules_rag = RulesRAG()
