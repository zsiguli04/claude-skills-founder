"""SQLite storage. Amounts are stored as decimal strings, never REAL."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('individual', 'trust')),
    resident INTEGER NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT NOT NULL,
    ownership_share TEXT NOT NULL,
    value TEXT NOT NULL,
    method TEXT NOT NULL,
    valuation_kind TEXT NOT NULL,
    valuation_inputs TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    UNIQUE (client_id, name)
);

CREATE TABLE IF NOT EXISTS debts (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    amount TEXT NOT NULL,
    secured_on_asset_id INTEGER REFERENCES assets(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);

-- A calculation stores its full input and output, so a report can be
-- reproduced and audited later even after the client's data changes.
CREATE TABLE IF NOT EXISTS calculations (
    id INTEGER PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    rule_key TEXT NOT NULL,
    rule_status TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    app_version TEXT NOT NULL,
    inputs TEXT NOT NULL,
    result TEXT NOT NULL,
    advisor_notes TEXT NOT NULL DEFAULT '',
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL
);

-- Append only. Nothing in the app updates or deletes rows here.
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id INTEGER,
    detail TEXT NOT NULL DEFAULT '{}',
    at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS audit_log_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append only'); END;
CREATE TRIGGER IF NOT EXISTS audit_log_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append only'); END;

CREATE INDEX IF NOT EXISTS idx_assets_client ON assets(client_id);
CREATE INDEX IF NOT EXISTS idx_debts_client ON debts(client_id);
CREATE INDEX IF NOT EXISTS idx_calculations_client ON calculations(client_id);
"""


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            self._migrate(conn)

    @staticmethod
    def _migrate(conn: sqlite3.Connection) -> None:
        """Add columns introduced after the first release to existing databases."""
        columns = {r["name"] for r in conn.execute("PRAGMA table_info(calculations)")}
        if "advisor_notes" not in columns:
            conn.execute("ALTER TABLE calculations ADD COLUMN advisor_notes TEXT NOT NULL DEFAULT ''")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def audit(self, conn: sqlite3.Connection, user_id: int | None, action: str, entity: str,
              entity_id: int | None, detail: dict[str, Any] | None = None) -> None:
        conn.execute(
            "INSERT INTO audit_log (user_id, action, entity, entity_id, detail, at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, action, entity, entity_id, json.dumps(detail or {}, ensure_ascii=False), now()),
        )
