import asyncio
import gzip
import json
from typing import Any, Dict, List

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.core.db import SessionLocal
from app.core.logging import logger
from app.models.card import Card
from app.services.scryfall import resolve_card_fields

BULK_DATA_URL = "https://api.scryfall.com/bulk-data"


async def fetch_bulk_data_uri(
    client: httpx.AsyncClient, bulk_type: str = "default_cards"
) -> str:
    """
    Looks up the current download URL for a Scryfall bulk-data file. Scryfall
    regenerates these daily and rotates the URL, so it always has to be
    looked up fresh rather than hardcoded. The field is `jsonl_download_uri`
    (a gzipped JSONL file) — confirmed against Scryfall's live API response,
    not assumed, after a first real run KeyError'd on a plain `download_uri`
    field that doesn't actually exist in the current API shape.
    """
    response = await client.get(BULK_DATA_URL)
    response.raise_for_status()
    for entry in response.json().get("data", []):
        if entry.get("type") == bulk_type:
            return entry["jsonl_download_uri"]
    raise ValueError(f"No {bulk_type!r} bulk-data entry found")


async def download_bulk_cards(
    client: httpx.AsyncClient, download_uri: str
) -> List[Dict[str, Any]]:
    """Downloads and parses a gzipped-JSONL Scryfall bulk-data file (one print per line)."""
    response = await client.get(download_uri)
    response.raise_for_status()
    decompressed = gzip.decompress(response.content)
    return [json.loads(line) for line in decompressed.splitlines() if line]


def _card_row(card_data: Dict[str, Any]) -> Dict[str, Any]:
    # Multi-faced cards (transform/modal-DFC/reversible/art-series) don't
    # always carry top-level name/type_line/image_uris — see
    # `resolve_card_fields`'s docstring for the live-API-confirmed cases.
    fields = resolve_card_fields(card_data)
    return {
        "id": card_data["id"],
        "name": fields["name"],
        "mana_cost": card_data.get("mana_cost"),
        "type_line": fields["type_line"],
        "oracle_text": card_data.get("oracle_text"),
        "colors": card_data.get("colors"),
        "produced_mana": card_data.get("produced_mana"),
        "image_uris": fields["image_uris"],
        "legalities": card_data.get("legalities"),
    }


async def upsert_cards(
    session: AsyncSession, cards: List[Dict[str, Any]], batch_size: int = 1000
) -> int:
    """
    Upserts card rows in batches. `sync_cards`' per-row select-then-update is
    fine for a handful of deck cards but far too slow for a ~30k+ row bulk
    file, so this splits each batch into "already exists" (bulk UPDATE, one
    executemany round trip) vs. "new" (bulk INSERT via add_all) instead of
    one round trip per row. Plain ORM update/insert rather than a
    dialect-specific ON CONFLICT upsert so this stays testable against the
    SQLite test engine, not just Postgres.
    """
    rows = [_card_row(c) for c in cards if c.get("id")]

    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        batch_ids = [row["id"] for row in batch]

        result = await session.execute(
            select(Card.id).where(col(Card.id).in_(batch_ids))
        )
        existing_ids = set(result.scalars().all())

        to_update = [row for row in batch if row["id"] in existing_ids]
        to_insert = [row for row in batch if row["id"] not in existing_ids]

        if to_update:
            await session.execute(update(Card), to_update)
        if to_insert:
            session.add_all(Card(**row) for row in to_insert)

        await session.commit()

    return len(rows)


async def run_ingestion() -> int:
    """
    Refreshes the local `Card` table from Scryfall's `default_cards` bulk
    file. Deliberately not wired into any container startup command or
    scheduler — run by hand (`uv run python -m
    app.ai.ingestion.scryfall_ingestion`) for now. Real recurring scheduling
    is deferred until there's an actual deployment target to schedule
    against (see PLAN.md's Deferred section).
    """
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        download_uri = await fetch_bulk_data_uri(client)
        logger.info(f"Downloading bulk cards from {download_uri}")
        cards = await download_bulk_cards(client, download_uri)
        logger.info(f"Downloaded {len(cards)} card entries")

    async with SessionLocal() as session:
        count = await upsert_cards(session, cards)

    logger.info(f"Upserted {count} cards")
    return count


if __name__ == "__main__":
    asyncio.run(run_ingestion())
