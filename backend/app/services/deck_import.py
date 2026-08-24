import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import httpx

from app.services.scryfall import ScryfallService

_LINE_PATTERN = re.compile(r"^(\d+)\s+(.+?)(?:\s+\((\w+)\)\s+(\d+))?\s*$")

_ZONE_HEADERS = {
    "deck": "main",
    "commander": "commander",
    "sideboard": "side",
    "maybe": "maybe",
}


@dataclass
class ParsedEntry:
    quantity: int
    name: str
    board: str
    set_code: Optional[str] = None
    collector_number: Optional[str] = None
    raw_line: str = ""


@dataclass
class ParsedDeck:
    name: Optional[str] = None
    entries: List[ParsedEntry] = field(default_factory=list)


def parse_decklist(text: str) -> ParsedDeck:
    """
    Parse a pasted decklist (simple list or MTGA export format) into structured
    entries. Unrecognized lines are silently skipped (not every line in a real
    paste is a card - headers, comments, blank lines).
    """
    deck = ParsedDeck()
    zone = "main"
    in_about = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()
        if lower == "about":
            in_about = True
            continue
        if lower in _ZONE_HEADERS:
            zone = _ZONE_HEADERS[lower]
            in_about = False
            continue
        if in_about and lower.startswith("name "):
            deck.name = line[len("name "):].strip()
            continue

        match = _LINE_PATTERN.match(line)
        if not match:
            continue

        quantity, name, set_code, collector_number = match.groups()
        deck.entries.append(
            ParsedEntry(
                quantity=int(quantity),
                name=name.strip(),
                board=zone,
                set_code=set_code,
                collector_number=collector_number,
                raw_line=line,
            )
        )

    return deck


@dataclass
class ResolvedEntry:
    card_id: str
    quantity: int
    board: str


_COLLECTION_CHUNK_SIZE = 75  # Scryfall's /cards/collection limit per request


async def resolve_entries(
    entries: List[ParsedEntry], scryfall: ScryfallService
) -> Tuple[List[ResolvedEntry], List[str]]:
    """
    Resolve parsed entries to Scryfall card IDs via the batch /cards/collection
    endpoint (up to 75 identifiers per request), not one search per entry - a
    60-card decklist used to mean 60+ sequential Scryfall requests, easily
    enough to trip their rate limit and 500 the whole import.

    Best-effort: entries that can't be resolved (not found, no match) are
    reported separately rather than failing the whole import.
    """
    if not entries:
        return [], []

    by_name: dict[str, List[ParsedEntry]] = {}
    by_printing: dict[Tuple[str, str], List[ParsedEntry]] = {}
    identifiers: List[dict] = []

    for entry in entries:
        if entry.set_code and entry.collector_number:
            key = (entry.set_code.lower(), entry.collector_number)
            by_printing.setdefault(key, []).append(entry)
            identifiers.append(
                {"set": entry.set_code.lower(), "collector_number": entry.collector_number}
            )
        else:
            key = entry.name.lower()
            by_name.setdefault(key, []).append(entry)
            identifiers.append({"name": entry.name})

    resolved: List[ResolvedEntry] = []
    resolved_entry_ids: set = set()

    for start in range(0, len(identifiers), _COLLECTION_CHUNK_SIZE):
        chunk = identifiers[start : start + _COLLECTION_CHUNK_SIZE]
        try:
            result = await scryfall.get_collection(chunk)
        except httpx.HTTPStatusError:
            continue  # everything in this chunk falls through to `missing` below

        for card in result.get("data", []):
            # Scryfall always returns the combined "Front // Back" name for
            # split/adventure/MDFC/transform cards, even when queried by the
            # front face alone (the way decklists normally spell them) - fall
            # back to matching on the front face so those cards resolve.
            full_name = card.get("name", "").lower()
            front_name = full_name.split(" // ")[0]
            matches = (
                by_printing.get(
                    (card.get("set", "").lower(), card.get("collector_number", "")), []
                )
                + by_name.get(full_name, [])
                + by_name.get(front_name, [])
            )
            for entry in matches:
                if id(entry) in resolved_entry_ids:
                    continue
                resolved_entry_ids.add(id(entry))
                resolved.append(
                    ResolvedEntry(
                        card_id=card["id"], quantity=entry.quantity, board=entry.board
                    )
                )

    missing = [e.raw_line for e in entries if id(e) not in resolved_entry_ids]
    return resolved, missing
