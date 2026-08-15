from unittest.mock import MagicMock

import pytest
from app.ai.ingestion.card_embedding_ingestion import (
    _chunk_for_card,
    embed_and_upsert,
    fetch_unique_cards,
)
from app.models.card import Card


@pytest.mark.asyncio
async def test_fetch_unique_cards_dedups_by_name(db_session) -> None:
    # Two printings of the same card (same name, different id) plus one
    # unrelated card -- should collapse to one row per unique name, picking
    # the lowest id, same as local_search_cards's own grouping.
    db_session.add_all(
        [
            Card(id="lightning-bolt-1", name="Lightning Bolt", type_line="Instant"),
            Card(id="lightning-bolt-2", name="Lightning Bolt", type_line="Instant"),
            Card(id="sol-ring-1", name="Sol Ring", type_line="Artifact"),
        ]
    )
    await db_session.commit()

    cards = await fetch_unique_cards(db_session)

    names = sorted(c.name for c in cards)
    assert names == ["Lightning Bolt", "Sol Ring"]
    bolt = next(c for c in cards if c.name == "Lightning Bolt")
    assert bolt.id == "lightning-bolt-1"


def test_chunk_for_card_embeds_name_type_and_oracle_text() -> None:
    card = Card(
        id="sol-ring-1",
        name="Sol Ring",
        type_line="Artifact",
        oracle_text="{T}: Add {C}{C}.",
    )

    chunk = _chunk_for_card(card)

    # Card *name* is the Chroma document id, not the row's Scryfall UUID --
    # this is what makes re-embedding idempotent across runs regardless of
    # which printing wins func.min(Card.id).
    assert chunk.id == "Sol Ring"
    assert chunk.text == "Sol Ring\nArtifact\n{T}: Add {C}{C}."
    # Chroma's upsert rejects an empty metadata dict outright (confirmed
    # against the live stack) -- metadata must be non-empty.
    assert chunk.metadata


def test_chunk_for_card_handles_missing_type_or_oracle_text() -> None:
    card = Card(id="x", name="Blank Card", type_line=None, oracle_text=None)

    chunk = _chunk_for_card(card)

    assert chunk.text == "Blank Card\n\n"


@pytest.mark.asyncio
async def test_embed_and_upsert_batches_and_calls_embedder_and_store() -> None:
    cards = [
        Card(id=f"card-{i}", name=f"Card {i}", type_line="Creature", oracle_text="")
        for i in range(5)
    ]
    embedder = MagicMock()
    store = MagicMock()

    total = await embed_and_upsert(cards, embedder, store, batch_size=2)

    assert total == 5
    # 5 cards at batch_size=2 -> 3 batches (2, 2, 1)
    assert embedder.embed.call_count == 3
    assert store.upsert.call_count == 3
    all_upserted_ids = [
        chunk.id for call in store.upsert.call_args_list for chunk in call.args[0]
    ]
    assert sorted(all_upserted_ids) == [f"Card {i}" for i in range(5)]
