import asyncio
import os
import re

import aiohttp
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# Re-define Embedding Function here to separate ingestion logic/prefixes if needed 
# or just reuse a shared class if imported. For script independence, we define it here.

class DocEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(
        self,
        # model_name: str = "nomic-ai/nomic-embed-text-v1"
        model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    ):
        self.model = SentenceTransformer(model_name, trust_remote_code=True, device="cpu")
        self.prefix_doc = "search_document: "

    def __call__(self, input: list[str]) -> list[list[float]]:
        # Ingestion time: We ALWAYS prefix with search_document:
        prefixed_input = [self.prefix_doc + text for text in input]
        embeddings = self.model.encode(prefixed_input, convert_to_tensor=False)
        return embeddings.tolist()

async def download_rules() -> str:
    """Downloads the comprehensive rules text."""
    url = "https://media.wizards.com/2026/downloads/MagicCompRules%2020260116.txt"
    print(f"Downloading rules from {url}...")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                print(f"Failed to download rules: Status {response.status}")
                return ""
            return await response.text(encoding='utf-8', errors='ignore')

def parse_rules(text: str) -> list[dict]:
    """Parses rules into chunks."""
    if not text:
        return []
        
    chunks = []
    lines = text.splitlines()
    current_rule = None
    current_text = []

    rule_pattern = re.compile(r'^(\d{3}\.\d+[a-z]?)')

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        match = rule_pattern.match(line)
        if match:
            if current_rule:
                chunks.append({
                    "id": current_rule,
                    "text": "\n".join(current_text)
                })
            current_rule = match.group(1)
            current_text = [line]
        else:
            if current_rule:
                current_text.append(line)
    
    if current_rule:
        chunks.append({
            "id": current_rule,
            "text": "\n".join(current_text)
        })
    
    if not chunks:
        print(f"Text length: {len(text)}")
        print(f"First 500 chars: {text[:500]}")
    
    print(f"Parsed {len(chunks)} rules.")
    return chunks

def ingest_rules(chunks: list[dict]):
    """Embeds rules and saves to ChromaDB."""
    if not chunks:
        print("No chunks to ingest.")
        return

    print("Initializing ChromaDB and Embedding Model...")
    persist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", ".chroma")
    os.makedirs(persist_path, exist_ok=True)
    
    client = chromadb.PersistentClient(path=persist_path)
    
    # Use the DOC embedding function
    ef = DocEmbeddingFunction()
    
    # Get or create collection
    # Note: If it exists with different settings, you might want to delete using client.delete_collection("mtg_rules")
    # For now, we assume clean slate or overwrite logic via upsert
    collection = client.get_or_create_collection(name="mtg_rules", embedding_function=ef)
    
    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [{"id": c["id"]} for c in chunks]

    batch_size = 1
    max_len = max(len(d) for d in documents)
    avg_len = sum(len(d) for d in documents) / len(documents)
    print(f"Max doc length: {max_len} chars")
    print(f"Avg doc length: {avg_len} chars")
    
    print(f"Ingesting {len(documents)} documents in batches of {batch_size}...")
    
    for i in range(0, len(documents), batch_size):
        end = min(i + batch_size, len(documents))
        print(f"Ingesting {i} to {end}...")
        collection.upsert(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end]
        )
    
    print("Ingestion complete.")

if __name__ == "__main__":
    asyncio.run(
        asyncio.to_thread(
            lambda: ingest_rules(
                parse_rules(
                    asyncio.run(download_rules())
                )
            )
        )
    )
