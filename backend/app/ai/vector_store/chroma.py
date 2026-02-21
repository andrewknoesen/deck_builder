from typing import Any, Dict, List, Optional, cast

import chromadb
from app.ai.types import PipelineContext, ProcessedChunk
from app.ai.vector_store.base import EmbeddingModel, VectorStore
from chromadb.config import Settings
from app.core.config import settings


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: str = "mtg_rules",
        embedding_model: Optional[EmbeddingModel] = None,
    ):
        host = host or settings.CHROMA_HOST
        port = port or settings.CHROMA_PORT

        print(f"Connecting to ChromaDB at {host}:{port}...")
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )
        self.embedding_model = embedding_model

    def upsert(self, chunks: List[ProcessedChunk], context: PipelineContext) -> None:
        if not chunks:
            return

        ids = [c.id for c in chunks]
        # Ensure embeddings exist
        valid_chunks = [c for c in chunks if c.embedding is not None]
        if len(valid_chunks) != len(chunks):
            print(
                f"Warning: {len(chunks) - len(valid_chunks)} chunks have no embeddings and will be skipped."
            )

        if not valid_chunks:
            return

        embeddings: Any = [c.embedding for c in valid_chunks]
        texts = [c.text for c in valid_chunks]
        metadatas: Any = [c.metadata for c in valid_chunks]

        self.collection.upsert(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )
        print(f"Upserted {len(valid_chunks)} chunks to ChromaDB.")

    def search(
        self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[ProcessedChunk]:
        """
        Searches the vector store.
        """
        if not self.embedding_model:
            raise ValueError(
                "EmbeddingModel required for search to convert query text to vector."
            )

        # Create a dummy chunk to embed the query
        dummy_chunk = ProcessedChunk(id="query", text=query)
        self.embedding_model.embed(
            [dummy_chunk], PipelineContext(execution_id="search", timestamp=0)
        )
        if not dummy_chunk.embedding:
            raise ValueError("Failed to generate embedding for query")

        query_embedding = dummy_chunk.embedding

        results = self.collection.query(
            query_embeddings=cast(List[Any], [query_embedding]),
            n_results=limit,
            where=filters,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        if results["ids"] and results["documents"] and results["metadatas"]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]

            for i in range(len(ids)):
                chunks.append(
                    ProcessedChunk(
                        id=ids[i],
                        text=docs[i],
                        metadata=cast(Dict[str, Any], metadatas[i] or {}),
                    )
                )
        return chunks

    def delete(self, ids: List[str], context: PipelineContext) -> None:
        self.collection.delete(ids=ids)
