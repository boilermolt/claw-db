# Usage (Facts DB helper + workflow)

## Helper script
The helper wraps `memory_db.py` and points to the Bobby‑drive DB by default.

```bash
/media/boilerrat/Bobby/claw-db/scripts/memory-db.sh search --q "\"claw db\"" --limit 2
```

Default DB path:
```
/media/boilerrat/Bobby/claw-db/state/memory.db
```
Override with:
```bash
export CLOUD_MEMORY_DB=/path/to/memory.db
```

---

## Auto‑write convention (recommended)
After any **decision / deploy / preference / incident / config change**:

```bash
/media/boilerrat/Bobby/claw-db/scripts/memory-db.sh upsert-fact \
  --entity "project.avantis" \
  --key "risk_profile" \
  --value "bootstrap-v1 active: z=1.1, min_risk=10, max_risk=25, lev=2.0, max_deployed=0.5" \
  --ttl-class active \
  --source "telegram"
```

Before answering recall/status questions:

```bash
/media/boilerrat/Bobby/claw-db/scripts/memory-db.sh search --q "risk_profile bootstrap-v1" --limit 5
```

---

## Suggested memory policy
- **Write to DB** for structured facts (settings, decisions, IDs, thresholds).
- **Write to markdown** (`memory/YYYY-MM-DD.md`) for narrative/log context.
- **Read DB first** for precise recall, then markdown/embeddings for nuance.

---

## TTL cheat sheet
- **permanent:** invariants, identities, hard rules
- **stable:** project setups, recurring workflows (90 days)
- **active:** current sprint/task context (14 days)
- **session:** debugging context (24 hours)
- **checkpoint:** pre‑flight state (~4 hours)
