import gzip
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.ai.ingestion.scryfall_ingestion import (
    download_bulk_cards,
    fetch_bulk_data_uri,
    upsert_cards,
)
from app.models.card import Card
from sqlmodel import select


def _mock_response(json_data):
    response = MagicMock()
    response.json.return_value = json_data
    response.raise_for_status = MagicMock()
    return response


def _mock_gzip_jsonl_response(rows):
    body = b"\n".join(json.dumps(row).encode() for row in rows)
    response = MagicMock()
    response.content = gzip.compress(body)
    response.raise_for_status = MagicMock()
    return response


@pytest.mark.asyncio
async def test_fetch_bulk_data_uri_finds_default_cards() -> None:
    client = AsyncMock()
    client.get.return_value = _mock_response(
        {
            "data": [
                {
                    "type": "oracle_cards",
                    "jsonl_download_uri": "https://example.com/oracle.jsonl.gz",
                },
                {
                    "type": "default_cards",
                    "jsonl_download_uri": "https://example.com/default.jsonl.gz",
                },
            ]
        }
    )

    uri = await fetch_bulk_data_uri(client)

    assert uri == "https://example.com/default.jsonl.gz"


@pytest.mark.asyncio
async def test_fetch_bulk_data_uri_raises_when_missing() -> None:
    client = AsyncMock()
    client.get.return_value = _mock_response({"data": []})

    with pytest.raises(ValueError):
        await fetch_bulk_data_uri(client)


@pytest.mark.asyncio
async def test_download_bulk_cards_returns_parsed_jsonl() -> None:
    client = AsyncMock()
    client.get.return_value = _mock_gzip_jsonl_response(
        [{"id": "abc", "name": "Test Card"}, {"id": "def", "name": "Other Card"}]
    )

    result = await download_bulk_cards(client, "https://example.com/default.jsonl.gz")

    assert result == [
        {"id": "abc", "name": "Test Card"},
        {"id": "def", "name": "Other Card"},
    ]


@pytest.mark.asyncio
async def test_upsert_cards_inserts_new_and_updates_existing(db_session) -> None:
    db_session.add(Card(id="sol-ring", name="Sol Ring (stale)", legalities={}))
    await db_session.commit()

    cards = [
        {
            "id": "sol-ring",
            "name": "Sol Ring",
            "mana_cost": "{1}",
            "type_line": "Artifact",
            "oracle_text": "Add {2}.",
            "colors": [],
            "produced_mana": ["C"],
            "legalities": {"commander": "legal"},
        },
        {
            "id": "lightning-bolt",
            "name": "Lightning Bolt",
            "mana_cost": "{R}",
            "type_line": "Instant",
            "oracle_text": "Lightning Bolt deals 3 damage to any target.",
            "colors": ["R"],
            "produced_mana": None,
            "legalities": {"modern": "legal"},
        },
    ]

    count = await upsert_cards(db_session, cards)

    assert count == 2
    result = await db_session.execute(select(Card).where(Card.id == "sol-ring"))
    sol_ring = result.scalar_one()
    assert sol_ring.name == "Sol Ring"
    assert sol_ring.legalities == {"commander": "legal"}

    result = await db_session.execute(select(Card).where(Card.id == "lightning-bolt"))
    bolt = result.scalar_one()
    assert bolt.name == "Lightning Bolt"


@pytest.mark.asyncio
async def test_upsert_cards_skips_entries_without_id(db_session) -> None:
    count = await upsert_cards(db_session, [{"name": "No ID Card"}])

    assert count == 0
