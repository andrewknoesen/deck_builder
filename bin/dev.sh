#!/bin/bash
cd "$(dirname "$0")/.."
(cd backend && uv sync)
./bin/start-compose.sh