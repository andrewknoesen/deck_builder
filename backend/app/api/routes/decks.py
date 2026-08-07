from typing import List

from app.api.deps import get_current_user
from app.core.db import get_db
from app.models.card import Card
from app.models.deck import (
    Deck,
    DeckCard,
    DeckCreate,
    DeckPublic,
    DeckUpdate,
)
from app.models.user import User
from app.schemas.deck_import import DeckImportRequest, DeckImportResponse
from app.services.deck_import import parse_decklist, resolve_entries
from app.services.scryfall import (
    ScryfallService,
    get_scryfall_service,
    resolve_card_fields,
)
from app.services.stats import calculate_stats
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

router = APIRouter()


async def sync_cards(db: AsyncSession, card_ids: List[str], scryfall: ScryfallService):
    """
    Ensure cards exist in the local database. Fetch missing ones from Scryfall.
    """
    if not card_ids:
        return

    # Check which cards exist and have been synced with produced_mana
    # We treat NULL produced_mana as "needs sync"
    result = await db.execute(
        select(Card.id)
        .where(col(Card.id).in_(card_ids))
        .where(col(Card.produced_mana).is_not(None))
    )
    existing_synced_ids = set(result.scalars().all())

    ids_to_fetch = list(set(card_ids) - existing_synced_ids)
    if not ids_to_fetch:
        return

    # Fetch missing cards from Scryfall
    scryfall_cards = await scryfall.get_cards_by_ids(ids_to_fetch)

    # Process fetched cards
    for card_data in scryfall_cards:
        # Check if card already exists (but was incomplete) to avoid PK violation
        # We can use upsert or just checking existence.
        # Since we filtered by "is_not(None)", the card MIGHT exist but have NULL.
        # So we should try to get it first or use merge.

        # Simpler approach: check if it exists in DB (even with NULL)
        existing_check = await db.execute(
            select(Card).where(Card.id == card_data["id"])
        )
        existing_card = existing_check.scalar_one_or_none()

        produced_mana = card_data.get("produced_mana", [])
        # Multi-faced cards (transform/modal-DFC/reversible/art-series) don't
        # always carry top-level name/type_line/image_uris — see
        # `resolve_card_fields`'s docstring for the live-API-confirmed cases.
        fields = resolve_card_fields(card_data)

        if existing_card:
            # Update existing
            existing_card.name = fields["name"]
            existing_card.mana_cost = card_data.get("mana_cost")
            existing_card.type_line = fields["type_line"]
            existing_card.oracle_text = card_data.get("oracle_text")
            existing_card.colors = card_data.get("colors")
            existing_card.produced_mana = produced_mana
            existing_card.image_uris = fields["image_uris"]
            existing_card.legalities = card_data.get("legalities")
            db.add(existing_card)
        else:
            # Create new
            card = Card(
                id=card_data["id"],
                name=fields["name"],
                mana_cost=card_data.get("mana_cost"),
                type_line=fields["type_line"],
                oracle_text=card_data.get("oracle_text"),
                colors=card_data.get("colors"),
                produced_mana=produced_mana,
                image_uris=fields["image_uris"],
                legalities=card_data.get("legalities"),
            )
            db.add(card)

    await db.commit()


@router.get("/", response_model=List[DeckPublic])
async def read_decks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve decks (fast, from local DB).
    """
    # Eager load cards AND the nested card definition
    result = await db.execute(
        select(Deck)
        .where(Deck.user_id == current_user.id)
        .options(
            selectinload(Deck.cards).selectinload(DeckCard.card)  # type: ignore[arg-type]
        )
    )
    decks = result.scalars().all()
    return decks


@router.post("/", response_model=DeckPublic)
async def create_deck(
    deck_in: DeckCreate,
    db: AsyncSession = Depends(get_db),
    scryfall: ScryfallService = Depends(get_scryfall_service),
    current_user: User = Depends(get_current_user),
):
    """
    Create new deck. Safely syncs cards to local DB first.
    """
    # 1. Sync cards to DB
    if deck_in.cards:
        card_ids = [dc.card_id for dc in deck_in.cards]
        await sync_cards(db, card_ids, scryfall)

    # 2. Create Deck
    db_deck = Deck.model_validate(
        deck_in, update={"cards": [], "user_id": current_user.id}
    )

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
        .options(selectinload(Deck.cards).selectinload(DeckCard.card))  # type: ignore[arg-type]
    )
    return result.scalar_one()


@router.post("/import", response_model=DeckImportResponse)
async def import_deck(
    import_in: DeckImportRequest,
    db: AsyncSession = Depends(get_db),
    scryfall: ScryfallService = Depends(get_scryfall_service),
    current_user: User = Depends(get_current_user),
):
    """
    Import a deck from pasted text (simple list or MTGA export format).
    Best-effort: cards that can't be resolved are reported as warnings
    instead of failing the whole import.
    """
    parsed = parse_decklist(import_in.text)
    resolved, missing = await resolve_entries(parsed.entries, scryfall)

    # Merge duplicate (card_id, board) pairs so a repeated line in the pasted
    # text can't violate DeckCard's (deck_id, card_id, board) primary key.
    merged: dict[tuple[str, str], int] = {}
    for entry in resolved:
        key = (entry.card_id, entry.board)
        merged[key] = merged.get(key, 0) + entry.quantity

    if merged:
        await sync_cards(db, [card_id for card_id, _ in merged], scryfall)

    title = import_in.name or parsed.name or "Imported Deck"
    db_deck = Deck(title=title, user_id=current_user.id)
    db_deck.cards = [
        DeckCard(card_id=card_id, quantity=quantity, board=board)
        for (card_id, board), quantity in merged.items()
    ]

    db.add(db_deck)
    await db.commit()
    await db.refresh(db_deck)

    return DeckImportResponse(id=db_deck.id, title=db_deck.title, missing_cards=missing)


@router.get("/{deck_id}", response_model=DeckPublic)
async def read_deck(
    deck_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get deck by ID (fast).
    """
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(Deck.cards).selectinload(DeckCard.card))  # type: ignore[arg-type]
    )
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return deck


@router.put("/{deck_id}", response_model=DeckPublic)
async def update_deck(
    deck_id: int,
    deck_in: DeckUpdate,
    db: AsyncSession = Depends(get_db),
    scryfall: ScryfallService = Depends(get_scryfall_service),
    current_user: User = Depends(get_current_user),
):
    """
    Update deck. Syncs new cards if added.
    """
    result = await db.execute(
        select(Deck).where(Deck.id == deck_id).options(selectinload(Deck.cards))  # type: ignore[arg-type]
    )
    db_deck = result.scalar_one_or_none()
    if not db_deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if db_deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

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
                    new_card = DeckCard.model_validate(
                        card_in, update={"deck_id": db_deck.id}
                    )
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
        .options(selectinload(Deck.cards).selectinload(DeckCard.card))  # type: ignore[arg-type]
    )
    return result.scalar_one()


@router.delete("/{deck_id}")
async def delete_deck(
    deck_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete deck.
    """
    result = await db.execute(select(Deck).where(Deck.id == deck_id))
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(deck)
    await db.commit()
    return {"status": "ok"}


@router.get("/{deck_id}/stats")
async def get_deck_stats(
    deck_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get deck statistics.
    """
    result = await db.execute(
        select(Deck)
        .where(Deck.id == deck_id)
        .options(selectinload(Deck.cards).selectinload(DeckCard.card))  # type: ignore[arg-type]
    )
    deck = result.scalar_one_or_none()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    stats = calculate_stats(deck)
    return stats
