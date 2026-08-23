import re


def calculate_cmc(mana_cost: str) -> float:
    """
    Parse a Scryfall-style mana cost string (e.g. "{2}{G}", "{X}{R}") into its
    mana value.

    - Generic-mana numbers, e.g. {2}, contribute their numeric value.
    - {X} contributes 0 (it has no value off the stack).
    - Every other {...} symbol (colored pips, hybrid, Phyrexian) contributes 1.
    """
    if not mana_cost:
        return 0

    cmc = 0
    # Count generic numbers e.g. {2}
    numbers = re.findall(r"\{(\d+)\}", mana_cost)
    for num in numbers:
        cmc += int(num)

    # Remove the generic-number symbols, then {X} (contributes 0), then count
    # every remaining {...} symbol as 1 (colored pips, hybrid, Phyrexian, etc).
    remaining = re.sub(r"\{(\d+)\}", "", mana_cost)
    remaining = re.sub(r"\{X\}", "", remaining, flags=re.IGNORECASE)
    pips = len(re.findall(r"\{.*?\}", remaining))
    cmc += pips

    return float(cmc)
