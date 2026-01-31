import os
from typing import List

import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer


class EmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, model_name: str = "Qwen/Qwen3-Embedding-0.6B"):
        self.model = SentenceTransformer(model_name, trust_remote_code=True, device="cpu")
        self.prefix_query = "search_query: "
        self.prefix_doc = "search_document: "

    def __call__(self, input: list[str]) -> list[list[float]]:
        # This function is used by Chroma for both query and doc embedding.
        # However, Chroma's EmbeddingFunction interface doesn't distinguish between the two contextually easily 
        # without inspecting stack or having separate functions.
        # OPTION: We assume this function is primarily used for QUERYING in this RAG class, 
        # and we manually handle document embedding in ingestion script. 
        # BUT Chroma calls this automatically if we pass it to collection.query().
        
        # Determine if inputs look like queries or docs? Hard to say.
        # Safe bet for Nomic v1 with Chroma:
        # If we use this for `query_texts`, we need the query prefix.
        # If we used it for `upsert`, we need doc prefix.
        
        # Hack/Simplification: 
        # We will assume this instance is used for QUERIES (runtime RAG).
        # We will strip prefixes if they double up, but generally prepend query prefix.
        
        prefixed_input = [self.prefix_query + text if not text.startswith(self.prefix_query) and not text.startswith(self.prefix_doc) else text for text in input]
        
        embeddings = self.model.encode(prefixed_input, convert_to_tensor=False)
        return embeddings.tolist()

class RulesRAG:
    def __init__(self):
        self._enabled = False
        try:
            persist_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", ".chroma")
            self.client = chromadb.PersistentClient(path=persist_path)
            
            # For query time, we use the embedding function that adds query prefixes
            self.ef = EmbeddingFunction()
            
            # We get the collection. 
            # Note: If existing collection has different embedding function metadata, this might warn.
            self.collection = self.client.get_collection(name="mtg_rules", embedding_function=self.ef)
            self._enabled = True
        except Exception as e:
            print(f"Failed to initialize RAG: {e}")
            self._enabled = False

    def query_rules(self, query: str, k: int = 5) -> List[str]:
        """
        Retrieves top-k relevant rules for the query.
        """
        if not self._enabled:
            return []
        
        try:
            # Query texts will be embedded by self.ef (which adds search_query: prefix)
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            if results and results['documents']:
                return results['documents'][0]
            return []
        except Exception as e:
            print(f"RAG Query validation failed: {e}")
            return []

# Singleton instance
# Note: Loading the model might take time/memory on import. 
# In production, we might want to delay load or wrap in a startup event.
# For now, we instantiate globally but try/except handles failures.
rules_rag = RulesRAG()
