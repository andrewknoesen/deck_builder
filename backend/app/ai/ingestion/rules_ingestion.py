import asyncio
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


def split_into_paragraph_segments(
    text: str,
    min_len: int = 200,
    max_len: int = 1000,
) -> List[Dict]:
    """
    Very generic paragraph-based splitter for RAG.
    - No assumption about rule numbers.
    - Works on arbitrary text (headers, glossary, examples, etc.).
    Returns a list of {id, text, metadata}.
    """
    # First, group lines into paragraphs separated by blank lines
    paragraphs = []
    buf: List[str] = []

    for line in text.splitlines():
        if line.strip() == "":
            if buf:
                paragraphs.append(" ".join(buf).strip())
                buf = []
        else:
            buf.append(line.strip())

    if buf:
        paragraphs.append(" ".join(buf).strip())

    # Then, merge / split paragraphs to get roughly min_len–max_len chars
    segments: List[Dict] = []
    current: List[str] = []
    current_len = 0
    seg_index = 0

    def flush_segment():
        nonlocal current, current_len, seg_index
        if not current:
            return
        seg_text = " ".join(current).strip()
        if not seg_text:
            return
        segments.append({
            "id": f"mtg-2026-seg-{seg_index}",
            "text": seg_text,
            "metadata": {
                "source": "mtg_comprehensive_rules_2026",
                "segment_index": seg_index,
            },
        })
        seg_index += 1
        current = []
        current_len = 0

    for p in paragraphs:
        if not p:
            continue

        # If paragraph is huge, chunk it by max_len
        if len(p) > max_len:
            start = 0
            while start < len(p):
                piece = p[start:start + max_len]
                segments.append({
                    "id": f"mtg-2026-seg-{seg_index}",
                    "text": piece.strip(),
                    "metadata": {
                        "source": "mtg_comprehensive_rules_2026",
                        "segment_index": seg_index,
                    },
                })
                seg_index += 1
                start += max_len
            continue

        # Normal paragraph: try to pack into the current segment
        if current_len + len(p) <= max_len:
            current.append(p)
            current_len += len(p)
        else:
            # Current segment is full enough; flush and start new
            flush_segment()
            current.append(p)
            current_len = len(p)

        # If segment is already “good enough”, flush eagerly
        if current_len >= min_len:
            flush_segment()

    flush_segment()
    return segments


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
    CHROMADB_HOST = "localhost"
    CHROMADB_PORT = 8001
    MODEL_NAME = "BAAI/bge-base-en-v1.5"
    MTG_RULES_FILE = None  # optional local override

    # 1) Load raw document text
    if MTG_RULES_FILE:
        print(f"Loading MTG rules from file: {MTG_RULES_FILE}")
        with open(MTG_RULES_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        print("Downloading MTG rules text...")
        content = asyncio.run(download_rules())

    if not content:
        print("No content; aborting.")
        return

    # 2) Split document into generic segments (no dict, no rule regex)
    print("Splitting document into segments...")
    segments = split_into_paragraph_segments(
        content,
        min_len=400,   # tune for your RAG
        max_len=1200,  # token-ish proxy
    )
    print(f"Prepared {len(segments)} segments")

    # 3) Embed segments
    print("\nGenerating embeddings...")
    embedded_segments = generate_embeddings_local(
        segments,
        model_name=MODEL_NAME,
        batch_size=16,
        device=None,
        use_mps=True,
    )

    # 4) Ingest into ChromaDB
    print("\nIngesting to ChromaDB...")
    db = MTGRulesVectorDB(
        host=CHROMADB_HOST,
        port=CHROMADB_PORT,
        embedding_model=MODEL_NAME,
    )
    db.add_segments(embedded_segments)

    stats = db.get_collection_stats()
    print(f"\n✅ Complete! Collection has {stats['total_segments']} segments")



if __name__ == "__main__":
    main()