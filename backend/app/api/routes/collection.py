from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, delete

from app.core.db import get_db
from app.models.user import User
from app.models.collection import CollectionCard
from app.models.card import Card
from app.schemas.collection import CollectionCardCreate, CollectionCardRead, CollectionCardUpdate
from app.api.deps import get_current_user
from app.services.scryfall import ScryfallService, get_scryfall_service

router = APIRouter()

@router.get("", response_model=List[CollectionCardRead])
async def read_collection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the current user's collection.
    """
    # Retrieve collection with card details eagerly loaded
    statement = select(CollectionCard).where(CollectionCard.user_id == current_user.id).options(selectinload(CollectionCard.card))
    
    result = await db.execute(statement)
    collection_items = result.scalars().all()
    return collection_items

@router.post("", response_model=CollectionCardRead)
async def add_to_collection(
    item_in: CollectionCardCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    scryfall: ScryfallService = Depends(get_scryfall_service),
):
    """
    Add a card to the collection. Upserts if already exists.
    """
    # Check if card exists in local DB, if not fetch and cache it
    card = await db.get(Card, item_in.card_id)
    if not card:
        # Fetch from Scryfall
        scryfall_card = await scryfall.get_card_by_id(item_in.card_id)
        # Create local Card
        # Map scryfall_card dict to Card model
        card = Card(
            id=scryfall_card["id"],
            name=scryfall_card["name"],
            mana_cost=scryfall_card.get("mana_cost"),
            type_line=scryfall_card.get("type_line"),
            oracle_text=scryfall_card.get("oracle_text"),
            colors=scryfall_card.get("colors"),
            image_uris=scryfall_card.get("image_uris"),
            scryfall_uri=scryfall_card.get("scryfall_uri"),
        )
        db.add(card)
        await db.commit()
        await db.refresh(card)

    # Check if user already has this card
    statement = select(CollectionCard).where(
        CollectionCard.user_id == current_user.id,
        CollectionCard.card_id == item_in.card_id
    ).options(selectinload(CollectionCard.card))
    result = await db.execute(statement)
    existing_item = result.scalars().first()

    if existing_item:
        existing_item.quantity += item_in.quantity
        db.add(existing_item)
        await db.commit()
        await db.refresh(existing_item)
        return existing_item
    else:
        new_item = CollectionCard(
            user_id=current_user.id,
            card_id=item_in.card_id,
            quantity=item_in.quantity
        )
        db.add(new_item)
        await db.commit()
        await db.refresh(new_item)
        # Manually set card for return
        new_item.card = card
        return new_item

@router.patch("/{collection_item_id}", response_model=CollectionCardRead)
async def update_collection_item(
    collection_item_id: int,
    item_in: CollectionCardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a collection item (e.g. quantity).
    """
    item = await db.get(CollectionCard, collection_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if item_in.quantity <= 0:
        await db.delete(item)
        await db.commit()
        return item
    
    item.quantity = item_in.quantity
    db.add(item)
    await db.commit()
    await db.refresh(item, attribute_names=["card"])
    return item

@router.delete("/{collection_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_collection(
    collection_item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove an item from the collection.
    """
    item = await db.get(CollectionCard, collection_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.delete(item)
    await db.commit()
