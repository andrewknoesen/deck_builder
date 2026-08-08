from typing import List

import httpx
from app.core.db import get_db
from app.models.card import Card
from app.models.deck import ScryfallCardPublic
from app.services.scryfall import ScryfallService, get_scryfall_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

router = APIRouter()

@router.get("/search")
async def search_cards(
    q: str, scryfall: ScryfallService = Depends(get_scryfall_service)
):
    """
    Search for cards using Scryfall.
    """
    try:
        data = await scryfall.search_cards(q)
        return data
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Scryfall error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/local-search", response_model=List[ScryfallCardPublic])
async def local_search_cards(q: str, db: AsyncSession = Depends(get_db)):
    """
    Search cards by name against the local, bulk-ingested Card table (see
    app/ai/ingestion/scryfall_ingestion.py) instead of proxying live to
    Scryfall's full-text search endpoint. Same underlying Scryfall data,
    served from the already-downloaded copy — for interactive typeahead
    (the deck-builder search box, one request per keystroke) this avoids an
    external network round trip entirely. Backed by a trigram index
    (migration 34f74e54c976); without it this same query is a multi-second
    sequential scan over ~116k rows, slower than just calling Scryfall.

    Grouping by name (picking one id per name) collapses reprints down to
    one row per card name, matching Scryfall's own default `unique=cards`
    search behavior. Written as a group-by-then-join rather than Postgres's
    DISTINCT ON so it stays testable against the SQLite test engine, same
    reasoning as upsert_cards() in app/ai/ingestion/scryfall_ingestion.py.
    """
    if not q.strip():
        return []
    matching_ids = (
        select(func.min(Card.id))
        .where(col(Card.name).ilike(f"%{q}%"))
        .group_by(col(Card.name))
        .order_by(col(Card.name))
        .limit(20)
    )
    result = await db.execute(
        select(Card).where(col(Card.id).in_(matching_ids)).order_by(col(Card.name))
    )
    return result.scalars().all()


@router.get("/{card_id}")
async def get_card(
    card_id: str, scryfall: ScryfallService = Depends(get_scryfall_service)
):
    """
    Get card by ID.
    """
    try:
        data = await scryfall.get_card_by_id(card_id)
        return data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Card not found")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Scryfall error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
