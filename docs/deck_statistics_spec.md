# MTG Deck Statistics Specification

This document defines the mathematical formulas, algorithms, and data structures required to implement the "Deck Stats" feature. It is intended for the Backend Engineer (FastAPI) and Frontend Engineer (React).

## 1. Mana Curve

**Goal**: Visualize the distribution of mana costs in the deck to assess early-game vs. late-game weight.

### Definition
*   **Filter**: Non-land cards only.
*   **X-Axis**: Converted Mana Cost (CMC) / Mana Value. Buckets: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7+`.
*   **Y-Axis**: Count of cards.

### Algorithm
1.  Iterate through all cards in the deck.
2.  Skip lands (`card.type_line` contains "Land" -- *Note: Be careful with Modal Double-Faced Cards, usually check front face*).
3.  Calculate CMC (already available on `Card` model as `mana_cost` string converted to number, or `cmc` field if we add it).
4.  Increment the count for the corresponding bucket.
5.  All cards with Cmc >= 7 go into the `7+` bucket.

### Backend Response Schema
```json
{
  "mana_curve": {
    "0": 2,
    "1": 4,
    "2": 10,
    "3": 8,
    "4": 6,
    "5": 4,
    "6": 2,
    "7+": 1
  },
  "average_cmc": 3.15
}
```

---

## 2. Color Distribution (Pip Count vs. Sources)

**Goal**: Ensure the deck has enough mana sources of a specific color to cast spells of that color reliably.

### A. Colored Pips (Requirements)
*   **Definition**: The total number of specific colored mana symbols ({W}, {U}, {B}, {R}, {G}) appearing in the mana costs of cards in the deck.
*   **Algorithm**:
    1.  Parse the `mana_cost` string of each card (e.g., `{1}{W}{W}` has 2 White pips).
    2.  Sum the occurrences of `{W}`, `{U}`, `{B}`, `{R}`, `{G}` across all mainboard cards.
    3.  Ignore generic mana `{1}`, `{X}`, etc.

### B. Mana Sources (Production)
*   **Definition**: The count of lands (and artifacts/dorks) that *produce* specific colors.
*   **Algorithm**:
    1.  Iterate through cards.
    2.  Use the `produced_mana` field (Array of strings, e.g., `["W", "U"]`).
    3.  Sum unique production capabilities. *Heuristic*: If a card produces multiple colors (e.g., Command Tower), increment for *all* those colors.

### Backend Response Schema
### C. Recommended Sources (Karsten's Heuristic)
*   **Goal**: Estimate how many sources of a color are needed to consistently cast spells of that color on curve (90% probability).
*   **Reference**: Based on Frank Karsten's "How Many Colored Mana Sources Do You Need?"
*   **Algorithm**:
    1.  For each color (W, U, B, R, G):
    2.  Identify the "most demanding" card in the deck for that color.
    3.  "Demand" is determined by the specific mana cost symbols and the card's CMC (Turn played).
    4.  Use the table below to find the recommended source count.

#### Lookup Table (Simplified)
| Cost Pattern | Example | Turn (CMC) | Rec. Sources (60-Card) | Rec. Sources (Commander) |
| :--- | :--- | :--- | :--- | :--- |
| **{C}** | {R} | 1 | 14 | 23 |
| **{1}{C}** | {1}{R} | 2 | 13 | 20 |
| **{C}{C}** | {R}{R} | 2 | 20 | 33 |
| **{2}{C}** | {2}{R} | 3 | 12 | 19 |
| **{1}{C}{C}** | {1}{R}{R} | 3 | 18 | 29 |
| **{C}{C}{C}** | {R}{R}{R} | 3 | 23 | 38 |
| **{3}{C}** | {3}{R} | 4 | 11 | 18 |
| **{2}{C}{C}** | {2}{R}{R} | 4 | 16 | 26 |

*   **Logic**:
    *   Iterate all non-land cards.
    *   For each color, find the max required sources from the table above based on that card's cost.
    *   Example: A deck has *Lightning Bolt* ({R}) and *Goblin Chainwhirler* ({R}{R}{R}).
        *   Bolt -> Needs 14.
        *   Chainwhirler -> Needs 23.
        *   Max Requirement for Red = 23.

### Backend Response Schema
```json
{
  "colors": {
    "W": { "pips": 12, "sources": 14, "recommended_sources": 18 },
    "U": { "pips": 24, "sources": 18, "recommended_sources": 18 },
    "B": { "pips": 0, "sources": 0, "recommended_sources": 0 },
    "R": { "pips": 8, "sources": 10, "recommended_sources": 13 },
    "G": { "pips": 0, "sources": 0, "recommended_sources": 0 },
    "C": { "pips": 5, "sources": 4, "recommended_sources": 0 }
  }
}
```

---

## 3. Land Count Recommendations

**Goal**: Suggest an optimal number of lands based on the deck's average CMC.

### Heuristic (Frank Karsten's Formula)

#### Standard / 60-Card Constructed
`Recommended Lands = 16 + 3.14 * AverageCMC`

#### Commander / 99-Card Constructed
`Recommended Lands = 31.42 + 3.13 * AverageCMC`

*   **Adjustments** (Applied to both):
    *   **Cheap Ramp**: -0.5 lands per cheap ramp spell (CMC <= 2, e.g., Llanowar Elves, Arcane Signet).
    *   **Cheap Draw/Cantrips**: -0.25 lands per cheap cantrip (CMC <= 2, e.g., Opt, Ponder).

### Algorithm
1.  Calculate `AverageCMC` of non-land cards.
2.  Count `Ramp` cards (heuristic: `type_line` contains "Creature" or "Artifact" AND `oracle_text` contains "add" AND `cmc` <= 2).
3.  Count `Cantrip` cards (heuristic: `oracle_text` contains "draw a card" AND `cmc` <= 2).
4.  Determine format (passed as argument or inferred from deck size).
    *   **If Commander (>80 cards)**:
        `Base = 31.42 + (3.13 * AvgCMC)`
    *   **Else (60 cards)**:
        `Base = 16 + (3.14 * AvgCMC)`
5.  Apply adjustments: `Count = Base - (0.5 * RampCount) - (0.25 * CantripCount)`.
6.  Clamp result logic:
    *   Commander: Clamp between 30 and 42.
    *   60-Card: Clamp between 18 and 30.

### Backend Response Schema
```json
{
  "recommendations": {
    "land_count": 24,
    "min_lands": 23,
    "max_lands": 25,
    "reasoning": "Based on average CMC of 3.1 and 4 ramp sources."
  }
}
```

---

## 4. Draw Probability (Hypergeometric Distribution)

**Goal**: Determine the likelihood of drawing specific cards or categories by a certain turn.

### Formula
The probability of drawing exactly $k$ successes in $n$ draws from a population $N$ containing $K$ total successes is:

$$ P(X=k) = \frac{\binom{K}{k} \binom{N-K}{n-k}}{\binom{N}{n}} $$

For "at least $k$" (cumulative), sum $P(X=i)$ for $i$ from $k$ to $\min(n, K)$.

*   **N (Population)**: Cards remaining in deck (Start: 60).
*   **K (Successes)**: Number of target cards in deck (e.g., 24 Lands).
*   **n (Draws)**: Opening hand (7) + Cards drawn per turn (Turn number - 1).
*   **k (Target)**: Minimum desired copies (e.g., At least 3 lands).

### Key Scenarios to Calculate
1.  **Mana Screw**: Probability of having < 2 lands in Opening Hand (7 cards).
2.  **Mana Flood**: Probability of having > 5 lands in Opening Hand.
3.  **On Curve**: Probability of having >= X lands by Turn X (for X=3, 4, 5).

### Backend Response Schema
```json
{
  "probabilities": {
    "opening_hand": {
      "lands_at_least_2": 0.85,
      "lands_at_least_3": 0.60,
      "lands_at_least_4": 0.30
    },
    "on_curve": {
      "turn_3_land_drop": 0.75,
      "turn_4_land_drop": 0.55
    }
  }
}
```

---

## 5. Proposed Backend Implementation

### Location
`backend/app/services/stats.py`

### Python Library
Use `scipy.stats.hypergeom` or implement the factorial formula manually for standard library purity (math.comb).

### API Endpoint
`GET /api/decks/{id}/stats`

#### Full Response Example
```json
{
  "deck_id": 12,
  "total_cards": 60,
  "mana_curve": { ... },
  "color_stats": { ... },
  "recommendations": { ... },
  "draw_odds": { ... }
}
```
