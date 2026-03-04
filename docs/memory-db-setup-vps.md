# Memory DB (SQLite + FTS5) — VPS Setup

This is the **local, API‑free memory store** used for structured facts/decisions. It is fast, searchable, and works without embeddings.

> **Goal:** replicate the same memory DB on boilerclaw (VPS) so memory lookups are local and cheap.

---

## What this DB is (and isn’t)
- **Is:** local SQLite + FTS5 “facts DB” for exact/near‑exact lookups.
- **Is not:** a vector DB or cloud API.
- **Embeddings are optional.** This DB works without them.

---

## Files you need
From the main host repo, copy these to the VPS:

- `scripts/memory_db_init.sql`
- `scripts/memory_db.py`

Recommended destination on VPS:
```
/home/boilerrat/clawd/scripts/
```

---

## 1) Create the DB
Default path:
```
/home/boilerrat/clawd/state/memory.db
```

Create it with:
```bash
sqlite3 /home/boilerrat/clawd/state/memory.db < /home/boilerrat/clawd/scripts/memory_db_init.sql
```

> **Note:** SQLite must be built with **FTS5** (common on most Linux distros).

---

## 2) (Optional) Override DB path
If you want a different location, set:
```bash
export CLOUD_MEMORY_DB=/path/to/memory.db
```

The CLI reads `CLOUD_MEMORY_DB` automatically.

---

## 3) Smoke test
Insert a test fact:
```bash
python3 /home/boilerrat/clawd/scripts/memory_db.py upsert-fact \
  --entity "memory" \
  --key "vps" \
  --value "boilerclaw initialized" \
  --ttl-class stable \
  --source "memory-db-setup-vps"
```

Search:
```bash
python3 /home/boilerrat/clawd/scripts/memory_db.py search --q "boilerclaw" --limit 5
```

If you see your row, you’re good.

---

## 4) How we use it
- **Write to DB** for decisions, conventions, stable facts.
- **Keep `MEMORY.md` lean** (only invariants).
- **Use daily logs** in `memory/YYYY-MM-DD.md` for raw notes.

Typical flow:
1) Log a short bullet in daily memory
2) Upsert a structured fact into the DB

---

## 5) Cleanup (TTL decay)
Rows expire by TTL class (permanent/stable/active/session/checkpoint). Run periodically:
```bash
python3 /home/boilerrat/clawd/scripts/memory_db.py expire
```

---

## Troubleshooting
**FTS error:** your SQLite lacks FTS5. Reinstall SQLite with FTS5 support.

**DB not found:** check `CLOUD_MEMORY_DB` or the default path.

---

## (Optional) Embeddings later
If you want fuzzy semantic recall later, add a **local embeddings** layer and keep this DB as the **first‑tier** fast path.
