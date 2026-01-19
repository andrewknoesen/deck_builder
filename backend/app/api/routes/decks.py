from typing import List, cast, Sequence

from app.core.db import get_db
from app.models.card import Card
from app.models.deck import (
    Deck,
    DeckCard,
    DeckCreate,
    DeckPublic,
    DeckUpdate,
)
from app.services.scryfall import ScryfallService, get_scryfall_service
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import QueryableAttribute, selectinload
from sqlmodel import select, col

router = APIRouter()


async def sync_cards(db: AsyncSession, card_ids: List[str], scryfall: ScryfallService):
    """
    Ensure cards exist in the local database. Fetch missing ones from Scryfall.
    """
    if not card_ids:
        return

    # Check which cards exist
    result = await db.execute(select(Card.id).where(col(Card.id).in_(card_ids)))
    existing_ids = set(result.scalars().all())
    
    missing_ids = list(set(card_ids) - existing_ids)
    if not missing_ids:
        return

    # Fetch missing cards from Scryfall
    scryfall_cards = await scryfall.get_cards_by_ids(missing_ids)
    
    # Insert new cards
    for card_data in scryfall_cards:
        # Map Scryfall JSON to Card model
        # Note: Scryfall JSON keys roughly match Card fields
        card = Card(
            id=card_data["id"],
            name=card_data["name"],
            mana_cost=card_data.get("mana_cost"),
            type_line=card_data.get("type_line"),
            oracle_text=card_data.get("oracle_text"),
            colors=card_data.get("colors"),
            image_uris=card_data.get("image_uris"),
        )
        db.add(card)
    
    await db.commit()


@router.get("/", response_model=List[DeckPublic])
async def read_decks(
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve decks (fast, from local DB).
    """
    # Eager load cards AND the nested card definition
    result = await db.execute(
        select(Deck).options(
            selectinload(Deck.cards).selectinload(DeckCard.card)
        )
    )
    decks = result.scalars().all()
    return decks


@router.post("/", response_model=DeckPublic)
async def create_deck(
    deck_in: DeckCreate, 
    db: AsyncSession = Depends(get_db),
    scryfall: ScryfallService = Depends(get_scryfall_service)
):
    """
    Create new deck. Safely syncs cards to local DB first.
    """
    # 1. Sync cards to DB
    if deck_in.cards:
        card_ids = [dc.card_id for dc in deck_in.cards]
        await sync_cards(db, card_ids, scryfall)

    # 2. Create Deck
    db_deck = Deck.model_validate(deck_in, update={"cards": []})

    # 3. Create DeckCards
    if deck_in.cards:
        db_deck.cards = [
            DeckCard.model_validate(card, update={"deck_id": db_deck.id})
            for card in deck_in.cards
        ]

    db.add(db_deck)
    await db.commit()
    await db.refresh(db_deck)

    # 4. Reload with relations
    result = await db.execute(
        select(Deck)
        .where(Deck.id == db_deck.id)
        .options(selectinload(Deck.cards).selectinload(DeckCard.card))
    )
    return result.scalar_one()


@router.get("/{deck_id}", response_model=DeckPublic)
async def read_deck(
    deck_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get deck by ID (fast).
    """
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(Deck.cards).selectinload(DeckCard.card))
    )
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.put("/{deck_id}", response_model=DeckPublic)
async def update_deck(
    deck_id: int, 
    deck_in: DeckUpdate, 
    db: AsyncSession = Depends(get_db),
    scryfall: ScryfallService = Depends(get_scryfall_service)
):
    """
    Update deck. Syncs new cards if added.
    """
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(Deck.cards))
    )
    db_deck = result.scalar_one_or_none()
    if not db_deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    # Sync any new cards in the update payload
    if deck_in.cards:
        card_ids = [dc.card_id for dc in deck_in.cards]
        await sync_cards(db, card_ids, scryfall)

    update_data = deck_in.model_dump(exclude_unset=True)

    if "cards" in update_data:
        # Replace strategy with manual merge to ensure updates persist
        if deck_in.cards is not None:
            existing_cards_map = {dc.card_id: dc for dc in db_deck.cards}
            new_cards_list = []
            
            for card_in in deck_in.cards:
                if card_in.card_id in existing_cards_map:
                    # Update existing item in place
                    existing_card = existing_cards_map[card_in.card_id]
                    existing_card.quantity = card_in.quantity
                    existing_card.board = card_in.board
                    new_cards_list.append(existing_card)
                else:
                    # Create new item
                    new_card = DeckCard.model_validate(card_in, update={"deck_id": db_deck.id})
                    new_cards_list.append(new_card)
            
            db_deck.cards = new_cards_list
        
        del update_data["cards"]

    db_deck.sqlmodel_update(update_data)
    db.add(db_deck)
    await db.commit()
    await db.refresh(db_deck)

    # Reload with deep relations
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(Deck.cards).selectinload(DeckCard.card))
    )
    return result.scalar_one()


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
