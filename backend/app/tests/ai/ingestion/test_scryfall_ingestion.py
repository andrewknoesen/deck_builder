import gzip
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.ai.ingestion.scryfall_ingestion import (
    _card_row,
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


def test_card_row_falls_back_to_card_faces_image_uris_for_transform_card() -> None:
    # Shaped like a real Scryfall bulk-data transform card: no top-level
    # `image_uris` (per-face images live under `card_faces` instead), but a
    # genuinely correct top-level "Front // Back" name/type_line that should
    # be kept as-is -- confirmed against the live API (Delver of Secrets //
    # Insectile Aberration) before writing this test.
    card_data = {
        "id": "delver-id",
        "name": "Delver of Secrets // Insectile Aberration",
        "mana_cost": "{U}",
        "type_line": "Creature — Human Wizard // Creature — Human Insect",
        "oracle_text": None,
        "colors": ["U"],
        "produced_mana": None,
        "legalities": {"modern": "legal"},
        "card_faces": [
            {
                "name": "Delver of Secrets",
                "type_line": "Creature — Human Wizard",
                "image_uris": {"normal": "https://example.com/front.jpg"},
            },
            {
                "name": "Insectile Aberration",
                "type_line": "Creature — Human Insect",
                "image_uris": {"normal": "https://example.com/back.jpg"},
            },
        ],
    }

    row = _card_row(card_data)

    assert row["name"] == "Delver of Secrets // Insectile Aberration"
    assert row["type_line"] == "Creature — Human Wizard // Creature — Human Insect"
    assert row["image_uris"] == {"normal": "https://example.com/front.jpg"}


def test_card_row_prefers_front_face_name_for_reversible_card() -> None:
    # Shaped like a real Scryfall "reversible_card" print (e.g. Command
    # Tower's alternate-frame Secret Lair reversible printing), where both
    # faces are literally the same card. Confirmed against the live API:
    # for this layout Scryfall's own top-level `name` is already the
    # doubled "X // X" form and `type_line` is missing entirely -- neither
    # is what should display, so both should fall back to the front face.
    card_data = {
        "id": "reversible-command-tower",
        "name": "Command Tower // Command Tower",
        "mana_cost": "",
        "oracle_text": None,
        "colors": [],
        "produced_mana": ["B", "G", "R", "U", "W"],
        "legalities": {"commander": "legal"},
        "card_faces": [
            {
                "name": "Command Tower",
                "type_line": "Land",
                "image_uris": {"normal": "https://example.com/front.jpg"},
            },
            {
                "name": "Command Tower",
                "type_line": "Land",
                "image_uris": {"normal": "https://example.com/back.jpg"},
            },
        ],
    }

    row = _card_row(card_data)

    assert row["name"] == "Command Tower"
    assert row["type_line"] == "Land"
    assert row["image_uris"] == {"normal": "https://example.com/front.jpg"}
