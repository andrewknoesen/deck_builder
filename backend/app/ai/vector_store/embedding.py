from typing import List, Optional

import torch
from app.ai.types import PipelineContext, ProcessedChunk
from app.ai.vector_store.base import EmbeddingModel
from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbedder(EmbeddingModel):
    """Local embedding using SentenceTransformers."""

    def __init__(
        self, model_name: str = "BAAI/bge-base-en-v1.5", device: Optional[str] = None
    ):
        self.model_name = model_name

        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        self.device = device

        print(f"Loading embedding model {model_name} on {device}...")
        try:
            self.model = SentenceTransformer(model_name, device=device)
        except Exception:
            print("Fallback to CPU")
            self.model = SentenceTransformer(model_name, device="cpu")

    def embed(
        self, chunks: List[ProcessedChunk], context: PipelineContext
    ) -> List[ProcessedChunk]:
        if not chunks:
            return []

        texts = [c.text for c in chunks]
        embeddings = self.model.encode(
            texts, convert_to_numpy=True, normalize_embeddings=True
        )

        for i, chunk in enumerate(chunks):
            chunk.embedding = embeddings[i].tolist()

        return chunks
