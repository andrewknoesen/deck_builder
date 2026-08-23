import random
from typing import Dict, Optional, Tuple

from app.models.deck import Deck
from app.models.goldfish import GameState, GoldfishActionIn, Zones
from app.services.mana import calculate_cmc

COMMANDER_LIKE_FORMATS = {"Commander", "Brawl", "Oathbreaker"}

# The action types that mutate a player's zones (library/hand/battlefield/
# graveyard/exile) and are therefore target-aware (`self`/`opponent`).
# `set_life` is deliberately excluded — it already has its own target
# handling via the separate life_total/opponent_life_total fields, which
# live outside Zones on both sides and predate this split (Phase 3b).
# `next_turn` is handled by the route directly, not here at all.
ZONE_MUTATING_ACTIONS = {"draw", "play_land", "cast", "move_zone", "shuffle"}


def _shuffled_library(deck: Deck) -> list[str]:
    library: list[str] = []
    for dc in deck.cards:
        if dc.board == "main":
            library.extend([dc.card_id] * dc.quantity)
    random.shuffle(library)
    return library


def build_initial_state(deck: Deck, opponent_deck: Optional[Deck] = None) -> GameState:
    """
    Shuffles the deck's own mainboard (expanded by quantity) into a virtual
    library and returns the starting state for a fresh goldfish session.
    Starting life follows the same Commander-like format set DeckBuilder.tsx
    already uses for its own commander-format checks. When `opponent_deck` is
    given, its mainboard is independently shuffled into `opponent_zones` the
    same way — the two libraries share no mutable state.
    """
    library = _shuffled_library(deck)
    life_total = 40 if (deck.format or "") in COMMANDER_LIKE_FORMATS else 20

    opponent_zones = None
    if opponent_deck is not None:
        opponent_zones = Zones(library=_shuffled_library(opponent_deck))

    return GameState(
        library=library,
        life_total=life_total,
        opponent_life_total=life_total,
        opponent_zones=opponent_zones,
    )


def draw_card(zones: Zones) -> Tuple[Zones, Optional[str]]:
    """
    Draws one card from the top of the library into hand. Returns the new
    zones and the drawn card's id (None if the library was empty). Shared by
    the `draw` action, the opening-hand deal, and `next_turn`'s auto-draw —
    "draw a card" is the same operation everywhere it happens. Takes a bare
    `Zones` (not a full `GameState`) so it works identically for a player's
    own zones or an opponent's `opponent_zones` — a `GameState` is-a `Zones`,
    so passing one through here is still valid.
    """
    next_zones = zones.model_copy(deep=True)
    if not next_zones.library:
        return next_zones, None
    card_id = next_zones.library.pop(0)
    next_zones.hand.append(card_id)
    return next_zones, card_id


def _plural(n: int) -> str:
    return "" if n == 1 else "s"


def draw_opening_hand(state: GameState, count: int = 7) -> Tuple[GameState, str]:
    """
    Draws up to `count` cards from the top of the library in one shot for the
    player, and — when `state.opponent_zones` is set — the same for the
    opponent, in the same combined node (simultaneous pre-game setup, not a
    turn exchange). Draws fewer (or none) on either side if that library
    doesn't have enough cards; never raises. Reads/writes `state.opponent_zones`
    directly rather than taking a second `Zones` argument, since by the time
    this runs `build_initial_state` has already populated it.
    """
    next_state = state
    drawn = 0
    for _ in range(count):
        next_state, card_id = draw_card(next_state)
        if card_id is None:
            break
        drawn += 1

    if next_state.opponent_zones is None:
        plural = _plural(drawn)
        return next_state, f"Drew opening hand ({drawn} card{plural})"

    opponent_zones = next_state.opponent_zones
    opponent_drawn = 0
    for _ in range(count):
        opponent_zones, card_id = draw_card(opponent_zones)
        if card_id is None:
            break
        opponent_drawn += 1
    next_state.opponent_zones = opponent_zones

    if drawn == count and opponent_drawn == count:
        label = f"Drew opening hands ({count} cards each)"
    else:
        label = (
            f"Drew opening hands ({drawn} card{_plural(drawn)}; "
            f"opponent drew {opponent_drawn} card{_plural(opponent_drawn)})"
        )
    return next_state, label


def apply_action(
    state: GameState,
    action: GoldfishActionIn,
    card_names: Dict[str, str],
    card_mana_costs: Dict[str, str],
) -> Tuple[GameState, str]:
    """
    Applies a structured action to a state snapshot and returns the resulting
    snapshot plus a human-readable label for the node. No legality checking —
    the user picks the action, this just moves cards between zones or adjusts
    life. Raises ValueError on data-integrity problems (e.g. moving a card
    that isn't actually in the zone it's claimed to be in, or targeting the
    opponent in a session with no opponent deck); the route turns that into a
    400.
    """
    next_state = state.model_copy(deep=True)

    def name_of(card_id: str) -> str:
        return card_names.get(card_id, card_id)

    target_zones: Optional[Zones] = None
    prefix = ""
    if action.type in ZONE_MUTATING_ACTIONS:
        target_zones = (
            next_state if action.target == "self" else next_state.opponent_zones
        )
        if target_zones is None:
            raise ValueError("This session has no opponent deck")
        prefix = "" if action.target == "self" else "Opponent: "

    if action.type == "draw":
        drawn_zones, card_id = draw_card(target_zones)
        if action.target == "self":
            next_state = drawn_zones
        else:
            next_state.opponent_zones = drawn_zones
        if card_id is None:
            return next_state, f"{prefix}Tried to draw with an empty library"
        return next_state, f"{prefix}Drew {name_of(card_id)}"

    if action.type in ("play_land", "cast"):
        if not action.card_id:
            raise ValueError("card_id is required for this action")
        if action.card_id not in target_zones.hand:
            raise ValueError("Card is not in hand")
        target_zones.hand.remove(action.card_id)
        target_zones.battlefield.append(action.card_id)
        if action.target == "opponent":
            next_state.opponent_zones = target_zones
        if action.type == "cast":
            cmc = int(calculate_cmc(card_mana_costs.get(action.card_id, "")))
            if action.target == "opponent":
                next_state.opponent_mana_spent += cmc
            else:
                next_state.mana_spent += cmc
        verb = "Played" if action.type == "play_land" else "Cast"
        return next_state, f"{prefix}{verb} {name_of(action.card_id)}"

    if action.type == "move_zone":
        if not action.card_id or not action.from_zone or not action.to_zone:
            raise ValueError("card_id, from_zone, and to_zone are required")
        source = target_zones.zone(action.from_zone)
        if action.card_id not in source:
            raise ValueError(f"Card is not in {action.from_zone}")
        source.remove(action.card_id)
        target_zones.zone(action.to_zone).append(action.card_id)
        if action.target == "opponent":
            next_state.opponent_zones = target_zones
        return (
            next_state,
            f"{prefix}Moved {name_of(action.card_id)} from {action.from_zone} to {action.to_zone}",
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
        random.shuffle(target_zones.library)
        if action.target == "opponent":
            next_state.opponent_zones = target_zones
        return next_state, f"{prefix}Shuffled library"

    # "next_turn" is handled by the route directly, not here — advancing the
    # turn is a node-metadata concern (GoldfishNode.turn_number), not a
    # GameState mutation, so it doesn't belong in a state-transform function.
    raise ValueError(f"Unknown action type: {action.type}")
