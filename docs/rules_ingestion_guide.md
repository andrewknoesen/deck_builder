
# Implementation Guide: MTG Rules Ingestion Pipeline

This guide details how to build the rules ingestion pipeline designed in `rules_ingestion_pipeline.md`.

## Prerequisites

Ensure you have the following dependencies installed (add to `backend/requirements.txt` or `pyproject.toml`):

```toml
dependencies = [
    # ... existing ...
    "chromadb>=0.4.22",
    "sentence-transformers>=2.3.0",
    "torch>=2.0.0",  # For embedding model
]
```

## Step-by-Step Implementation

### 1. Setup Data Directory
Ensure you have the raw rules file.
- **Path**: `references/MagicCompRules 20260116.txt` (or similar version).

### 2. Create Parsing Logic (`backend/app/ai/ingestion/rules_parser.py`)

Create a new module to handle the specific parsing of MTG rules.

```python
import re
from typing import List, Dict, Optional

# Regex config
# Captures "702.19b" and the rest of the line
RULE_PATTERN = re.compile(r"^(\d{3}\.(?:[\d]+[a-z]?)?)\.?\s+(.*)")
GLOSSARY_START_MARKER = "Glossary"
CREDITS_START_MARKER = "Credits"

def parse_rules_file(file_content: str) -> List[Dict]:
    """
    Parses the MTG Rules text file into structured chunks.
    """
    lines = file_content.splitlines()
    chunks = []
    
    current_section = "intro" # intro, rules, glossary, credits
    
    # 1. Split into sections (simplified)
    # You might need to iterate lines and detect headers "1. Game Concepts", etc.
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect Section Changes (this is heuristic, check file structure)
        if line == GLOSSARY_START_MARKER:
            current_section = "glossary"
            continue
        if line == CREDITS_START_MARKER:
            current_section = "credits"
            continue
            
        if current_section == "rules" or current_section == "intro":
            # Try to match a rule
            match = RULE_PATTERN.match(line)
            if match:
                current_section = "rules" # We found a rule, so we are in rules section
                rule_id = match.group(1)
                rule_text = match.group(2)
                
                chunks.append({
                    "id": rule_id,
                    "text": line, # Full text "702.19b Trample..."
                    "metadata": {
                        "type": "rule",
                        "rule_id": rule_id,
                        "section": "rules"
                    }
                })
            else:
                # Continuation text or headers? 
                # For MVP, maybe skip or attach to previous rule if indented?
                # A robust parser handles multi-line rules.
                pass
                
        elif current_section == "glossary":
            # Glossary parsing logic (Term \n Definition)
            pass
            
    return chunks
```

### 3. Implement Embeddings & Storage (`backend/app/ai/ingestion/rules_ingestion.py`)

Refactor the existing `rules_ingestion.py` to use the new parser.

```python
from app.ai.ingestion.rules_parser import parse_rules_file
from app.ai.ingestion.chroma_setup import MTGRulesVectorDB

def main():
    # 1. Load Content
    with open("references/MagicCompRules 20260116.txt", "r", encoding="utf-8") as f:
        content = f.read()

    # 2. Parse (Structured)
    print("Parsing rules...")
    chunks = parse_rules_file(content)
    print(f"Found {len(chunks)} rules.")

    # 3. Generate Embeddings (Re-use existing generate_embeddings_local)
    # Note: Ensure generate_embeddings_local handles the dict structure correctly
    embedded_chunks = generate_embeddings_local(chunks, model_name="BAAI/bge-large-en-v1.5")

    # 4. Ingest to Chroma
    db = MTGRulesVectorDB()
    db.add_segments(embedded_chunks)
```

## Verification Scenarios

1.  **Exact Match**: Search for "702.19".
    -   *Expected*: The top result should be exactly Rule 702.19.
2.  **Semantic Search**: Search for "Does deathtouch work with trample?".
    -   *Expected*: Should retrieve rules for Deathtouch (702.2) and Trample (702.19) and their interaction rule (702.2c).

## Next Steps
1.  Implement `rules_parser.py`.
2.  Update `rules_ingestion.py` to use it.
3.  Run ingestion.
4.  Update `tools.py` to query this new collection.
