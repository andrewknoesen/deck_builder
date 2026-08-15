import asyncio
from typing import List

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.ai.types import PipelineContext, ProcessedChunk
from app.ai.vector_store.base import EmbeddingModel, VectorStore
from app.ai.vector_store.chroma import ChromaVectorStore
from app.ai.vector_store.embedding import shared_embedder
from app.core.db import SessionLocal
from app.core.logging import logger
from app.models.card import Card

_CONTEXT = PipelineContext(execution_id="card_embedding_ingestion", timestamp=0)


async def fetch_unique_cards(session: AsyncSession) -> List[Card]:
    """
    One row per unique card name -- the same func.min(Card.id)-grouped-by-name
    query app/api/routes/cards.py's local_search_cards already uses, so this
    embeds exactly one representative printing per name instead of ~4x
    duplicate, near-identical oracle text across reprints.
    """
    unique_ids = select(func.min(Card.id)).group_by(col(Card.name))
    result = await session.execute(select(Card).where(col(Card.id).in_(unique_ids)))
    return list(result.scalars().all())


def _chunk_for_card(card: Card) -> ProcessedChunk:
    """
    Embeds name + type_line + oracle_text. Uses the card's *name* as the
    Chroma document ID (not the representative row's Scryfall UUID) so
    re-running this script upserts idempotently regardless of which printing
    ends up selected as "representative" on a given run. `metadata` must be
    non-empty -- Chroma's upsert rejects an empty dict outright (confirmed
    against the live stack, not assumed) -- so it carries the name too, even
    though it's not otherwise used today.
    """
    text = "\n".join([card.name, card.type_line or "", card.oracle_text or ""])
    return ProcessedChunk(id=card.name, text=text, metadata={"name": card.name})


async def embed_and_upsert(
    cards: List[Card],
    embedder: EmbeddingModel,
    store: VectorStore,
    batch_size: int = 500,
) -> int:
    """Embeds and upserts cards in batches into the given vector store."""
    chunks = [_chunk_for_card(card) for card in cards]

    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        embedder.embed(batch, _CONTEXT)
        store.upsert(batch, _CONTEXT)
        total += len(batch)
        logger.info(f"Embedded and upserted {total}/{len(chunks)} cards")

    return total


async def run_ingestion() -> int:
    """
    Embeds every unique card name in the local Card table (populated by
    app.ai.ingestion.scryfall_ingestion) into the 'mtg_cards' Chroma
    collection. A separate, manual script from scryfall_ingestion.py --
    embedding tens of thousands of card texts through a local
    sentence-transformer model is a materially slower step than that
    script's pure-DB upsert, so it's not folded in (see PLAN.md's Phase 5
    Design section). Entry point: `uv run python -m
    app.ai.ingestion.card_embedding_ingestion`, run by hand after
    scryfall_ingestion.py whenever the card data's been refreshed.
    """
    store = ChromaVectorStore(
        embedding_model=shared_embedder, collection_name="mtg_cards"
    )

    async with SessionLocal() as session:
        cards = await fetch_unique_cards(session)

    logger.info(f"Found {len(cards)} unique card names to embed")
    total = await embed_and_upsert(cards, shared_embedder, store)
    logger.info(f"Card embedding ingestion complete: {total} cards upserted")
    return total


if __name__ == "__main__":
    asyncio.run(run_ingestion())
