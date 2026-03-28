#!/bin/bash
cd "$(dirname "$0")/.."
uv sync --all-groups --all-packages
cd backend
uv lock --frozen
cd ..
./bin/start-compose.sh