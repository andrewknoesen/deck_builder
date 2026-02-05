from typing import Dict, List

import chromadb
import torch
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class MTGRulesVectorDB:
    """ChromaDB-based vector store for MTG rules (segment-based for RAG)."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "mtg_rules",
        embedding_model: str = "BAAI/bge-base-en-v1.5",
    ):
        # Connect to ChromaDB (HTTP client for K8s deployment)
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        # Load embedding model for query-time embeddings
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = SentenceTransformer(embedding_model, device=device)
        
        # Create/get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:construction_ef": 128,
                "hnsw:search_ef": 64,
            },
        )
    
    def add_segments(self, chunks: List[Dict]):
        """
        Ingest MTG rules segments into ChromaDB.

        Args:
            chunks: List of dicts with:
                - 'id': unique string id for the segment
                - 'text': segment text
                - 'metadata': arbitrary metadata dict
                - 'embedding': precomputed embedding vector (list[float])
        """
        ids = [chunk["id"] for chunk in chunks]
        embeddings = [chunk["embedding"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        
        print(f"✓ Added {len(chunks)} segments to ChromaDB")
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        section_filter: str = None,
    ) -> List[Dict]:
        """
        Semantic search over MTG rules segments.

        Args:
            query: Natural language query.
            n_results: Number of results to return.
            section_filter: Optional filter on metadata['section'].

        Returns:
            List of matching segments with metadata and scores.
        """
        query_instruction = (
            "Represent this question for searching relevant Magic: The Gathering rules: "
        )
        query_embedding = self.model.encode(
            query_instruction + query,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).tolist()
        
        where_clause = {"section": section_filter} if section_filter else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "distances", "metadatas", "ids"],
        )
        
        formatted_results: List[Dict] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        dists = results.get("distances", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        
        for i in range(len(ids)):
            formatted_results.append({
                "id": ids[i],
                "text": docs[i],
                "metadata": metas[i],
                "distance": dists[i],
                "relevance_score": 1 - dists[i],
            })
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        count = self.collection.count()
        return {
            "total_segments": count,
            "collection_name": self.collection.name,
            "metadata": self.collection.metadata,
        }
