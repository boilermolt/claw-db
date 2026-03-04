PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS facts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity TEXT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  tags TEXT,
  ttl_class TEXT NOT NULL DEFAULT 'stable',
  confidence REAL,
  source TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  expires_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS facts_entity_key ON facts(entity, key);
CREATE INDEX IF NOT EXISTS facts_expires_at ON facts(expires_at);

-- FTS5 virtual table
CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
  entity,
  key,
  value,
  tags,
  content='facts',
  content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
  INSERT INTO facts_fts(rowid, entity, key, value, tags)
  VALUES (new.id, new.entity, new.key, new.value, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
  INSERT INTO facts_fts(facts_fts, rowid, entity, key, value, tags)
  VALUES('delete', old.id, old.entity, old.key, old.value, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS facts_au AFTER UPDATE ON facts BEGIN
  INSERT INTO facts_fts(facts_fts, rowid, entity, key, value, tags)
  VALUES('delete', old.id, old.entity, old.key, old.value, old.tags);
  INSERT INTO facts_fts(rowid, entity, key, value, tags)
  VALUES (new.id, new.entity, new.key, new.value, new.tags);
END;
