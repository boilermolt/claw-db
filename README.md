# claw-db

Local-first memory database for OpenClaw: **SQLite + FTS5** with TTL and a tiny CLI.

This repo contains **everything needed to replicate the memory DB system** on another host (e.g., boilerclaw VPS).

## Contents
- `scripts/memory_db_init.sql` — schema + FTS5 + triggers
- `scripts/memory_db.py` — CLI (upsert/search/get/expire)
- `scripts/memory-db.sh` — helper wrapper (default DB path on Bobby drive)
- `docs/memory-db-setup-vps.md` — step-by-step VPS setup
- `docs/usage.md` — helper usage + memory policy

## Quick start
```bash
# 1) Create DB
sqlite3 /home/boilerrat/clawd/state/memory.db < scripts/memory_db_init.sql

# 2) Smoke test
python3 scripts/memory_db.py upsert-fact \
  --entity "memory" \
  --key "vps" \
  --value "boilerclaw initialized" \
  --ttl-class stable \
  --source "claw-db README"

python3 scripts/memory_db.py search --q "boilerclaw" --limit 5
```

## Notes
- **No API required.** Fully local.
- SQLite must include **FTS5**.
- DB path defaults to `/home/boilerrat/clawd/state/memory.db`.
  Override with `CLOUD_MEMORY_DB`.

## License
MIT
