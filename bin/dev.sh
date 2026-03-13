#!/bin/bash
cd "$(dirname "$0")/.."
uv sync --all-groups --all-packages

./bin/start-compose.sh