# from functools import lru_cache

from typing import List, Optional

from app.ai.rag.base import RAGService
from app.ai.types import ProcessedChunk
from app.ai.vector_store.base import EmbeddingModel
from app.ai.vector_store.chroma import ChromaVectorStore
from app.ai.vector_store.embedding import SentenceTransformerEmbedder, shared_embedder


class RulesRAG(RAGService):
    """Retrieval-Augmented Generation for MTG Rules."""

    def __init__(self, embedder: Optional[EmbeddingModel] = None):
        self._enabled = False
        try:
            # Accept an injected embedder (e.g. the shared_embedder singleton)
            # so this doesn't load its own redundant copy of the model when a
            # second RAGService (CardRAG) also needs one; falls back to
            # constructing its own so this still works called standalone.
            self.embedder = embedder or SentenceTransformerEmbedder()
            self.store = ChromaVectorStore(embedding_model=self.embedder)
            self._enabled = True
        except Exception as e:
            print(f"Failed to initialize RAG: {e}")
            self._enabled = False

    def query(self, text: str, k: int = 5, filters: dict = None) -> List[str]:
        """
        Retrieves top-k relevant rules for the query.
        Returns a list of rule texts.
        """
        if not self._enabled:
            return []

        try:
            chunks: List[ProcessedChunk] = self.store.search(
                text, limit=k, filters=filters
            )
            return [chunk.text for chunk in chunks]
        except Exception as e:
            print(f"RAG Query validation failed: {e}")
            return []

    def query_glossary(self, term: str, k: int = 3) -> List[str]:
        """
        Retrieves glossary definitions for a term.
        """
        return self.query(term, k=k, filters={"type": "glossary"})


# @lru_cache()
# def get_rules_rag() -> RulesRAG:
#     return RulesRAG()

rules_rag = RulesRAG(embedder=shared_embedder)
