#!/usr/bin/env bash
set -euo pipefail
DB_PATH="${CLOUD_MEMORY_DB:-/media/boilerrat/Bobby/claw-db/state/memory.db}"
PY="/home/boilerrat/clawd/scripts/memory_db.py"
exec python3 "$PY" --db "$DB_PATH" "$@"
