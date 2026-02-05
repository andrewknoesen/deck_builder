import asyncio
import re
from typing import Dict, List, Optional

import aiohttp
import torch
from sentence_transformers import SentenceTransformer

from app.ai.ingestion.chroma_setup import MTGRulesVectorDB


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

def load_mtg_rules(file_path: Optional[str] = None) -> dict:
    """Load and parse MTG Comprehensive Rules"""
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = asyncio.run(download_rules())
    
    # Parse rules by section number (e.g., "100.1", "704.5k")
    # Rules are numbered hierarchically
    pattern = r'(\d+\.\d+[a-z]*)\.\s+(.*?)(?=\n\d+\.\d+[a-z]*\.|$)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    rules = {}
    for rule_num, rule_text in matches:
        rules[rule_num] = {
            'number': rule_num,
            'text': rule_text.strip(),
            'section': rule_num.split('.')[0]  # e.g., "704" from "704.5k"
        }
    print(rules)
    return rules

def chunk_rules_for_embedding(rules: dict, context_window: int = 512) -> list:
    """
    Chunk rules intelligently for embedding
    Best practice: 500-1000 tokens per chunk for semantic coherence
    """
    chunks = []
    
    for rule_num, rule_data in rules.items():
        # For each rule, create a chunk with context
        section = rule_data['section']
        chunk_text = f"Rule {rule_num}: {rule_data['text']}"
        
        chunks.append({
            'id': rule_num,
            'text': chunk_text,
            'metadata': {
                'rule_number': rule_num,
                'section': section,
                'type': 'comprehensive_rule'
            }
        })
    
    return chunks

def generate_embeddings_local(
    chunks: List[Dict], 
    model_name: str = "BAAI/bge-large-en-v1.5",
    batch_size: int = 16,  # Reduced for CPU
    device: Optional[str] = None,
    use_mps: bool = True  # Use Apple Metal Performance Shaders
) -> List[Dict]:
    """
    Generate embeddings using local Hugging Face model
    Optimized for Mac (including Apple Silicon)
    
    Recommended models for MTG rules (semantic search):
    - BAAI/bge-large-en-v1.5: 1024 dims, excellent for English text (Top choice)
    - BAAI/bge-base-en-v1.5: 768 dims, faster, still very good
    - sentence-transformers/all-mpnet-base-v2: 768 dims, popular baseline
    - intfloat/e5-large-v2: 1024 dims, instruction-following embeddings
    
    Args:
        chunks: List of chunk dictionaries with 'text' and 'metadata'
        model_name: HuggingFace model identifier
        batch_size: Batch size for encoding (16 recommended for Mac CPU)
        device: 'cuda', 'mps', 'cpu', or None (auto-detect)
        use_mps: Try to use Apple Metal Performance Shaders if available
    """
    
    # Auto-detect best device for Mac
    if device is None:
        if use_mps and torch.backends.mps.is_available():
            device = "mps"  # Apple Silicon GPU acceleration
            print("✓ Using Apple Metal Performance Shaders (MPS) for GPU acceleration")
        elif torch.cuda.is_available():
            device = "cuda"
            print("✓ Using CUDA GPU")
        else:
            device = "cpu"
            print("⚠ Using CPU (consider reducing batch_size to 8-16)")
    
    print(f"Loading model {model_name} on {device}...")
    
    # For MPS, need to handle potential compatibility issues
    try:
        model = SentenceTransformer(model_name, device=device)
    except Exception as e:
        if device == "mps":
            print(f"⚠ MPS failed ({e}), falling back to CPU")
            device = "cpu"
            model = SentenceTransformer(model_name, device=device)
        else:
            raise
    
    # Extract texts for batch encoding
    texts = [chunk['text'] for chunk in chunks]
    
    print(f"Generating embeddings for {len(texts)} chunks...")
    
    # Adjust batch size based on device
    if device == "cpu":
        batch_size = min(batch_size, 16)  # Cap at 16 for CPU
        print(f"Using batch_size={batch_size} for CPU processing")
    
    # Generate embeddings in batches with progress
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True  # Important for cosine similarity
    )
    
    # Attach embeddings to chunks
    embedded_chunks = []
    for chunk, embedding in zip(chunks, embeddings):
        chunk['embedding'] = embedding.tolist()  # Convert numpy to list for JSON serialization
        chunk['embedding_model'] = model_name
        chunk['embedding_dim'] = len(embedding)
        embedded_chunks.append(chunk)
    
    print(f"✓ Generated {len(embedded_chunks)} embeddings with {embeddings.shape[1]} dimensions")
    
    return embedded_chunks

def main():
    # Configuration
    CHROMADB_HOST = "localhost"
    CHROMADB_PORT = 8001
    MTG_RULES_FILE = None
    MODEL_NAME = "BAAI/bge-base-en-v1.5"
    
    print("Loading MTG rules...")
    rules = load_mtg_rules(MTG_RULES_FILE)
    chunks = chunk_rules_for_embedding(rules)
    print(f"Loaded {len(chunks)} rules")
    
    # Use your generate_embeddings_local function (it's better!)
    print("\nGenerating embeddings...")
    embedded_chunks = generate_embeddings_local(
        chunks,
        model_name=MODEL_NAME,
        batch_size=16,
        device=None,  # Auto-detect
        use_mps=True
    )
    
    print("\nIngesting to ChromaDB...")
    db = MTGRulesVectorDB(
        host=CHROMADB_HOST,
        port=CHROMADB_PORT,
        embedding_model=MODEL_NAME
    )
    
    db.add_rules(embedded_chunks)
    
    stats = db.get_collection_stats()
    print(f"\n✅ Complete! Collection has {stats['total_rules']} rules")


if __name__ == "__main__":
    main()