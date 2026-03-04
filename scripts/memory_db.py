#!/usr/bin/env python3

"""memory_db.py — Tiny SQLite/FTS5 memory store (facts DB)

This is the v1 implementation from docs/db-memory-plan.md:
- local-first
- structured facts (entity/key/value)
- FTS5 search
- TTL classes + optional expiry cleanup

Safety:
- Do NOT store secrets (keys, passwords, cookies, seed phrases).
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

DEFAULT_DB = os.environ.get("CLOUD_MEMORY_DB") or "/home/boilerrat/clawd/state/memory.db"

TTL_DEFAULT_DAYS = {
    "permanent": None,
    "stable": 90,
    "active": 14,
    "session": 1,
    "checkpoint": 0.1667,  # ~4 hours
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def compute_expires_at(ttl_class: str, now: datetime) -> Optional[str]:
    days = TTL_DEFAULT_DAYS.get(ttl_class)
    if days is None:
        return None
    seconds = int(days * 86400)
    exp = now + timedelta(seconds=seconds)
    return exp.replace(microsecond=0).isoformat()


@dataclass
class Fact:
    entity: str
    key: str
    value: str
    tags: Optional[str] = None
    ttl_class: str = "stable"
    confidence: Optional[float] = None
    source: Optional[str] = None


def connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def upsert_fact(con: sqlite3.Connection, fact: Fact) -> None:
    now = datetime.now(timezone.utc)
    now_iso = now.replace(microsecond=0).isoformat()
    expires_at = compute_expires_at(fact.ttl_class, now)

    # Upsert on (entity,key)
    con.execute(
        """
        INSERT INTO facts(entity, key, value, tags, ttl_class, confidence, source, created_at, updated_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entity, key) DO UPDATE SET
          value=excluded.value,
          tags=COALESCE(excluded.tags, facts.tags),
          ttl_class=excluded.ttl_class,
          confidence=COALESCE(excluded.confidence, facts.confidence),
          source=COALESCE(excluded.source, facts.source),
          updated_at=excluded.updated_at,
          expires_at=excluded.expires_at
        """,
        (
            fact.entity,
            fact.key,
            fact.value,
            fact.tags,
            fact.ttl_class,
            fact.confidence,
            fact.source,
            now_iso,
            now_iso,
            expires_at,
        ),
    )
    con.commit()


def get_fact(con: sqlite3.Connection, entity: str, key: str) -> Optional[sqlite3.Row]:
    row = con.execute(
        "SELECT * FROM facts WHERE entity=? AND key=?",
        (entity, key),
    ).fetchone()
    return row


def search(con: sqlite3.Connection, q: str, limit: int) -> list[sqlite3.Row]:
    # Use FTS5 match; join back to facts.
    rows = con.execute(
        """
        SELECT f.*
        FROM facts_fts
        JOIN facts f ON f.id = facts_fts.rowid
        WHERE facts_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (q, limit),
    ).fetchall()
    return rows


def expire(con: sqlite3.Connection, dry_run: bool = False) -> int:
    now = utc_now_iso()
    rows = con.execute(
        "SELECT id FROM facts WHERE expires_at IS NOT NULL AND expires_at < ?",
        (now,),
    ).fetchall()
    if dry_run:
        return len(rows)
    con.execute(
        "DELETE FROM facts WHERE expires_at IS NOT NULL AND expires_at < ?",
        (now,),
    )
    con.commit()
    return len(rows)


def refresh_ttl(con: sqlite3.Connection, ids: Iterable[int]) -> None:
    # Refresh expiry on retrieval (refresh-on-access)
    now = datetime.now(timezone.utc)
    now_iso = now.replace(microsecond=0).isoformat()
    for _id in ids:
        row = con.execute("SELECT ttl_class FROM facts WHERE id=?", (_id,)).fetchone()
        if not row:
            continue
        ttl_class = row["ttl_class"]
        exp = compute_expires_at(ttl_class, now)
        con.execute(
            "UPDATE facts SET updated_at=?, expires_at=? WHERE id=?",
            (now_iso, exp, _id),
        )
    con.commit()


def print_rows(rows: list[sqlite3.Row], as_json: bool = False) -> None:
    if as_json:
        out = [dict(r) for r in rows]
        print(json.dumps(out, indent=2, sort_keys=True))
        return

    for r in rows:
        print(f"[{r['ttl_class']}] {r['entity']}.{r['key']} = {r['value']}")
        src = r["source"] if "source" in r.keys() else None
        if src:
            print(f"  source: {src}")
        exp = r["expires_at"] if "expires_at" in r.keys() else None
        if exp:
            print(f"  expires_at: {exp}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=DEFAULT_DB, help=f"Path to SQLite DB (default: {DEFAULT_DB})")

    sub = p.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("upsert-fact")
    up.add_argument("--entity", required=True)
    up.add_argument("--key", required=True)
    up.add_argument("--value", required=True)
    up.add_argument("--tags")
    up.add_argument("--ttl-class", default="stable", choices=list(TTL_DEFAULT_DAYS.keys()))
    up.add_argument("--confidence", type=float)
    up.add_argument("--source")

    getp = sub.add_parser("get")
    getp.add_argument("--entity", required=True)
    getp.add_argument("--key", required=True)

    sp = sub.add_parser("search")
    sp.add_argument("--q", required=True)
    sp.add_argument("--limit", type=int, default=5)
    sp.add_argument("--json", action="store_true")
    sp.add_argument("--refresh", action="store_true", help="Refresh TTL on returned rows")

    ex = sub.add_parser("expire")
    ex.add_argument("--dry-run", action="store_true")

    args = p.parse_args()

    con = connect(args.db)

    if args.cmd == "upsert-fact":
        upsert_fact(
            con,
            Fact(
                entity=args.entity,
                key=args.key,
                value=args.value,
                tags=args.tags,
                ttl_class=args.ttl_class,
                confidence=args.confidence,
                source=args.source,
            ),
        )
        print("OK")
        return

    if args.cmd == "get":
        row = get_fact(con, args.entity, args.key)
        if not row:
            print("NOT_FOUND")
            return
        print_rows([row])
        return

    if args.cmd == "search":
        rows = search(con, args.q, args.limit)
        if args.refresh and rows:
            refresh_ttl(con, [int(r["id"]) for r in rows])
        print_rows(rows, as_json=args.json)
        return

    if args.cmd == "expire":
        n = expire(con, dry_run=args.dry_run)
        print(n)
        return


if __name__ == "__main__":
    main()
