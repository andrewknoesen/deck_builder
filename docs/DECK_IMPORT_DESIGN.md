# Deck Import Feature Design

This document outlines the design for importing decks via text paste (MTGA format).

## 1. Feature Overview

Users can import a deck by pasting a text list into the application. The system parses the list, resolves card identifiers using Scryfall (or local cache), and creates a new deck in the database.

### Supported Format (MTGA & Common Text)
The parser handles the following common formats:

**Simple List:**
```text
4 Blanchwood Prowler
3 Swamp
```

**MTGA Export:**
```text
Deck
4 Blanchwood Prowler (BRO) 172
3 Swamp (ONE) 211
...
Sideboard
2 Gnaw to the Bone (ISD) 183
```

**Meta-data Headers:**
- `About` / `Name [Name]`: Used to pre-fill the deck name.
- `Deck` / `Commander` / `Sideboard`: Used to determine card destination.

## 2. Frontend Design

### Component: `DeckImportModal`
- **Trigger**: "Import Deck" button on the "My Decks" dashboard.
- **UI Elements**:
  - `TextArea`: Large input field for pasting text.
  - `Input`: Deck Name (optional, auto-filled if "Name" found in text).
  - `Button`: "Import" (triggers API).
  - `Progress/Error Display`: Shows parsing errors or "Importing..." state.

### UX Flow
1. User clicks "Import Deck".
2. User pastes text and clicks "Import".
3. Frontend sends `POST /api/v1/decks/import`.
4. On success: Redirect to the new `DeckBuilder` page for that deck.
5. On failure: Show specific lines that failed to parse or card names not found.

## 3. Backend Design

### API Endpoint
- **Method**: `POST`
- **Path**: `/api/v1/decks/import`
- **Request Body**:
  ```json
  {
    "text": "string (raw text content)",
    "name": "string (optional override)"
  }
  ```
- **Response**:
  ```json
  {
    "id": 123,
    "name": "Dredge",
    "missing_cards": ["Card Name A"] // Warnings if any
  }
  ```

### Parsing Logic (Python)
1. **Normalization**: specific headers (`Deck`, `Sideboard`, `Commander`) switch the "current zone" state. `Name` header sets deck name.
2. **Regex Strategy**:
   - Pattern: `^(\d+)\s+(.+?)(?:\s+\((\w+)\)\s+(\d+))?\s*$`
   - Group 1: Quantity
   - Group 2: Name (trim trailing spaces)
   - Group 3 (Optional): Set Code
   - Group 4 (Optional): Collector Number
3. **Resolution**:
   - If Set/CN provided: Look up specific printing via Scryfall API (`set` + `cn`).
   - If Name only: Use Scryfall "Named" search (fuzzy or exact). 
   - **Optimization**: Batch Scryfall requests or check local DB for existing `scryfall_id`.

## 4. Task Breakdown

### Backend Agent
- [ ] Create `POST /api/v1/decks/import` endpoint.
- [ ] Implement text parser (Regex for MTGA/Simple formats).
- [ ] Implement Scryfall resolution logic (handle missing Set/CN by defaulting to latest printing or basic search).
- [ ] Transactionality: Valid cards are added, invalid ones returned as warnings, or fail whole batch (User Preference? Default to "Best Effort").

### Frontend Agent
- [ ] Create `DeckImportModal` component.
- [ ] precise validation feedback (e.g., "Line 5: Invalid format").
- [ ] Integrate with `api/decks.ts`.

### Shared
- [ ] Update `Deck` model to ensure it supports rapid insertion of cards.
