from typing import List, cast

from app.core.db import get_db
from app.models.deck import (
    Deck,
    DeckCard,
    DeckCreate,
    DeckPublic,
    DeckUpdate,
    ScryfallCardPublic,
)
from app.services.scryfall import ScryfallService, get_scryfall_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import QueryableAttribute, selectinload
from sqlmodel import select

router = APIRouter()


async def enrich_deck(deck: Deck, scryfall: ScryfallService) -> DeckPublic:
    card_ids = [dc.card_id for dc in deck.cards]
    if not card_ids:
        return DeckPublic.model_validate(deck)

    scryfall_cards = await scryfall.get_cards_by_ids(card_ids)
    scryfall_map = {c["id"]: c for c in scryfall_cards}

    # Use model_validate to get started, then manually add cards
    deck_public = DeckPublic.model_validate(deck)
    for dc_public in deck_public.cards:
        if dc_public.card_id in scryfall_map:
            dc_public.card = ScryfallCardPublic.model_validate(
                scryfall_map[dc_public.card_id]
            )

    return deck_public


@router.get("/", response_model=List[DeckPublic])
async def read_decks(
    db: AsyncSession = Depends(get_db),
    scryfall: ScryfallService = Depends(get_scryfall_service),
):
    """
    Retrieve decks.
    """
    result = await db.execute(
        select(Deck).options(selectinload(cast(QueryableAttribute, Deck.cards)))
    )
    decks = result.scalars().all()
    return [await enrich_deck(deck, scryfall) for deck in decks]


@router.post("/", response_model=DeckPublic)
async def create_deck(deck_in: DeckCreate, db: AsyncSession = Depends(get_db)):
    """
    Create new deck.
    """
    # Create the deck object without the nested cards first
    db_deck = Deck.model_validate(deck_in, update={"cards": []})

    # Add nested cards if any
    if deck_in.cards:
        db_deck.cards = [
            DeckCard.model_validate(card, update={"deck_id": db_deck.id})
            for card in deck_in.cards
        ]

    db.add(db_deck)
    await db.commit()
    await db.refresh(db_deck)

    # Reload with cards joined
    result = await db.execute(
        select(Deck)
        .where(Deck.id == db_deck.id)
        .options(selectinload(cast(QueryableAttribute, Deck.cards)))
    )
    db_deck = result.scalar_one()

    # Enrich with Scryfall data
    scryfall = await anext(get_scryfall_service())
    return await enrich_deck(db_deck, scryfall)


@router.get("/{deck_id}", response_model=DeckPublic)
async def read_deck(
    deck_id: int,
    db: AsyncSession = Depends(get_db),
    scryfall: ScryfallService = Depends(get_scryfall_service),
):
    """
    Get deck by ID.
    """
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(cast(QueryableAttribute, Deck.cards)))
    )
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return await enrich_deck(deck, scryfall)


@router.put("/{deck_id}", response_model=DeckPublic)
async def update_deck(
    deck_id: int, deck_in: DeckUpdate, db: AsyncSession = Depends(get_db)
):
    """
    Update deck.
    """
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(cast(QueryableAttribute, Deck.cards)))
    )
    db_deck = result.scalar_one_or_none()
    if not db_deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    update_data = deck_in.model_dump(exclude_unset=True)

    if "cards" in update_data:
        # Simple approach for POC: replace all cards
        # In a real app, you might want a more surgical sync
        if deck_in.cards:
            db_deck.cards = [
                DeckCard.model_validate(card, update={"deck_id": db_deck.id})
                for card in deck_in.cards
            ]
        else:
            db_deck.cards = []

        del update_data["cards"]

    db_deck.sqlmodel_update(update_data)
    db.add(db_deck)
    await db.commit()
    await db.refresh(db_deck)

    # Enrich with Scryfall data
    scryfall = await anext(get_scryfall_service())
    return await enrich_deck(db_deck, scryfall)


@router.delete("/{deck_id}")
async def delete_deck(deck_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete deck.
    """
    result = await db.execute(select(Deck).where(Deck.id == deck_id))
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    await db.delete(deck)
    await db.commit()
    return {"status": "ok"}


@router.get("/{deck_id}/stats")
def get_deck_stats(deck_id: int):
    """
    Get deck statistics.
    """
    return {"message": f"Deck stats placeholder for: {deck_id}"}
