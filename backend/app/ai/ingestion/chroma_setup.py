# chromadb_setup.py

from typing import Dict, List

import chromadb
import torch
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


class MTGRulesVectorDB:
    """ChromaDB-based vector store for MTG rules"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        collection_name: str = "mtg_rules",
        embedding_model: str = "BAAI/bge-base-en-v1.5"
    ):
        # Connect to ChromaDB (HTTP client for K8s deployment)
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Load embedding model
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = SentenceTransformer(embedding_model, device=device)
        
        # Create/get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",  # Cosine similarity
                "hnsw:construction_ef": 128,  # Build quality
                "hnsw:search_ef": 64  # Query quality
            }
        )
    
    def add_rules(self, chunks: List[Dict]):
        """
        Ingest MTG rules into ChromaDB
        
        Args:
            chunks: List of dicts with 'text', 'metadata', 'embedding'
        """
        
        ids = [chunk['metadata']['rule_number'] for chunk in chunks]
        embeddings = [chunk['embedding'] for chunk in chunks]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        # Batch upsert (handles updates automatically)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✓ Added {len(chunks)} rules to ChromaDB")
    
    def search_rules(
        self,
        query: str,
        n_results: int = 5,
        section_filter: str = None
    ) -> List[Dict]:
        """
        Search MTG rules using semantic similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            section_filter: Optional section number to filter by (e.g., "704")
        
        Returns:
            List of matching rules with metadata
        """
        
        # Generate query embedding
        query_instruction = "Represent this question for searching relevant Magic: The Gathering rules: "
        query_embedding = self.model.encode(
            query_instruction + query,
            convert_to_numpy=True,
            normalize_embeddings=True
        ).tolist()
        
        # Build where clause for filtering
        where_clause = {"section": section_filter} if section_filter else None
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause,
            include=["documents", "distances", "metadatas"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "rule_number": results['ids'][0][i],
                "text": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i],
                "relevance_score": 1 - results['distances'][0][i]  # Convert to similarity
            })
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        count = self.collection.count()
        return {
            "total_rules": count,
            "collection_name": self.collection.name,
            "metadata": self.collection.metadata
        }
