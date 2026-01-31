#!/bin/bash
# Navigate to the backend directory (parent of the scripts directory where this file resides)
cd "$(dirname "$0")/.."

# Source .env file if it exists to get HF_TOKEN
if [ -f .env ]; then
    echo "Loading .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Run ingestion and test using paths relative to backend/
PYTORCH_ENABLE_MPS_FALLBACK=1 uv run scripts/ingest_rules.py
uv run scripts/test_rules_agent.py "What are the parts of a turn?"
