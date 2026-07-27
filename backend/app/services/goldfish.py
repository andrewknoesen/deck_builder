import random
from typing import Dict, Optional, Tuple

from app.models.deck import Deck
from app.models.goldfish import GameState, GoldfishActionIn

COMMANDER_LIKE_FORMATS = {"Commander", "Brawl", "Oathbreaker"}


def build_initial_state(deck: Deck) -> GameState:
    """
    Shuffles the deck's own mainboard (expanded by quantity) into a virtual
    library and returns the starting state for a fresh goldfish session.
    Starting life follows the same Commander-like format set DeckBuilder.tsx
    already uses for its own commander-format checks.
    """
    library: list[str] = []
    for dc in deck.cards:
        if dc.board == "main":
            library.extend([dc.card_id] * dc.quantity)
    random.shuffle(library)

    life_total = 40 if (deck.format or "") in COMMANDER_LIKE_FORMATS else 20
    return GameState(
        library=library, life_total=life_total, opponent_life_total=life_total
    )


def draw_card(state: GameState) -> Tuple[GameState, Optional[str]]:
    """
    Draws one card from the top of the library into hand. Returns the new
    state and the drawn card's id (None if the library was empty). Shared by
    the `draw` action, the opening-hand deal, and `next_turn`'s auto-draw —
    "draw a card" is the same operation everywhere it happens.
    """
    next_state = state.model_copy(deep=True)
    if not next_state.library:
        return next_state, None
    card_id = next_state.library.pop(0)
    next_state.hand.append(card_id)
    return next_state, card_id


def draw_opening_hand(state: GameState, count: int = 7) -> Tuple[GameState, str]:
    """
    Draws up to `count` cards from the top of the library in one shot — used
    to auto-deal the opening hand when a session starts. Draws fewer (or
    none) if the library doesn't have enough cards; never raises.
    """
    next_state = state
    drawn = 0
    for _ in range(count):
        next_state, card_id = draw_card(next_state)
        if card_id is None:
            break
        drawn += 1
    plural = "" if drawn == 1 else "s"
    return next_state, f"Drew opening hand ({drawn} card{plural})"


def apply_action(
    state: GameState, action: GoldfishActionIn, card_names: Dict[str, str]
) -> Tuple[GameState, str]:
    """
    Applies a structured action to a state snapshot and returns the resulting
    snapshot plus a human-readable label for the node. No legality checking —
    the user picks the action, this just moves cards between zones or adjusts
    life. Raises ValueError on data-integrity problems (e.g. moving a card
    that isn't actually in the zone it's claimed to be in); the route turns
    that into a 400.
    """
    next_state = state.model_copy(deep=True)

    def name_of(card_id: str) -> str:
        return card_names.get(card_id, card_id)

    if action.type == "draw":
        drawn_state, card_id = draw_card(state)
        if card_id is None:
            return drawn_state, "Tried to draw with an empty library"
        return drawn_state, f"Drew {name_of(card_id)}"

    if action.type in ("play_land", "cast"):
        if not action.card_id:
            raise ValueError("card_id is required for this action")
        if action.card_id not in next_state.hand:
            raise ValueError("Card is not in hand")
        next_state.hand.remove(action.card_id)
        next_state.battlefield.append(action.card_id)
        verb = "Played" if action.type == "play_land" else "Cast"
        return next_state, f"{verb} {name_of(action.card_id)}"

    if action.type == "move_zone":
        if not action.card_id or not action.from_zone or not action.to_zone:
            raise ValueError("card_id, from_zone, and to_zone are required")
        source = next_state.zone(action.from_zone)
        if action.card_id not in source:
            raise ValueError(f"Card is not in {action.from_zone}")
        source.remove(action.card_id)
        next_state.zone(action.to_zone).append(action.card_id)
        return (
            next_state,
            f"Moved {name_of(action.card_id)} from {action.from_zone} to {action.to_zone}",
        )

    if action.type == "set_life":
        if action.life_total is None:
            raise ValueError("life_total is required for this action")
        if action.target == "opponent":
            old_life = next_state.opponent_life_total
            next_state.opponent_life_total = action.life_total
            return next_state, f"Opponent life: {old_life} → {action.life_total}"
        old_life = next_state.life_total
        next_state.life_total = action.life_total
        return next_state, f"Life: {old_life} → {action.life_total}"

    if action.type == "shuffle":
        random.shuffle(next_state.library)
        return next_state, "Shuffled library"

    # "next_turn" is handled by the route directly, not here — advancing the
    # turn is a node-metadata concern (GoldfishNode.turn_number), not a
    # GameState mutation, so it doesn't belong in a state-transform function.
    raise ValueError(f"Unknown action type: {action.type}")
