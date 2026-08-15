from typing import List, Optional

from app.ai.rag.base import RAGService
from app.ai.types import ProcessedChunk
from app.ai.vector_store.base import EmbeddingModel
from app.ai.vector_store.chroma import ChromaVectorStore
from app.ai.vector_store.embedding import SentenceTransformerEmbedder, shared_embedder


class CardRAG(RAGService):
    """Retrieval-Augmented Generation over MTG card oracle text -- finds
    cards by what they DO semantically, not by exact text match. Same shape
    as RulesRAG, pointed at a separate 'mtg_cards' Chroma collection."""

    def __init__(self, embedder: Optional[EmbeddingModel] = None):
        self._enabled = False
        try:
            # Accept an injected embedder (the shared_embedder singleton) so
            # this doesn't load a second, redundant copy of the model
            # alongside RulesRAG's; falls back to constructing its own so
            # this still works called standalone.
            self.embedder = embedder or SentenceTransformerEmbedder()
            self.store = ChromaVectorStore(
                embedding_model=self.embedder, collection_name="mtg_cards"
            )
            self._enabled = True
        except Exception as e:
            print(f"Failed to initialize CardRAG: {e}")
            self._enabled = False

    def query(self, text: str, k: int = 5, filters: dict = None) -> List[str]:
        """
        Retrieves top-k semantically relevant cards for the query.
        Returns a list of embedded card texts (name + type line + oracle text).
        """
        if not self._enabled:
            return []

        try:
            chunks: List[ProcessedChunk] = self.store.search(
                text, limit=k, filters=filters
            )
            return [chunk.text for chunk in chunks]
        except Exception as e:
            print(f"CardRAG Query failed: {e}")
            return []


card_rag = CardRAG(embedder=shared_embedder)
