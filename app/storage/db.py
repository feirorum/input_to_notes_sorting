"""SQLite state: captures, audit entries, learned examples, entities.

The vault Markdown files are the human-facing source of truth for *content*;
SQLite is the source of truth for *state* (what's been processed, what can be
undone, what corrections we've learned). They're kept in sync by the router.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional

_lock = threading.Lock()


SCHEMA = """
CREATE TABLE IF NOT EXISTS captures (
    id          TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL,
    source      TEXT NOT NULL,
    source_type TEXT NOT NULL,
    status      TEXT NOT NULL,
    processed   INTEGER NOT NULL DEFAULT 0,
    text        TEXT NOT NULL,
    inbox_path  TEXT NOT NULL,
    decision    TEXT            -- last computed Decision (JSON), for review/confirm
);

CREATE TABLE IF NOT EXISTS audit (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    capture_id   TEXT NOT NULL,
    processed_at TEXT NOT NULL,
    action       TEXT NOT NULL,
    destination  TEXT,
    confidence   REAL NOT NULL,
    undo_available INTEGER NOT NULL DEFAULT 0,
    undone       INTEGER NOT NULL DEFAULT 0,
    reasoning    TEXT,
    change_made  TEXT,
    undo_payload TEXT            -- JSON: how to reverse the change
);

CREATE TABLE IF NOT EXISTS examples (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT NOT NULL,
    title           TEXT,
    text            TEXT NOT NULL,
    destination_key TEXT NOT NULL,
    note_path       TEXT,
    note            TEXT
);

CREATE TABLE IF NOT EXISTS entities (
    name            TEXT NOT NULL,
    destination_key TEXT NOT NULL,
    note_path       TEXT NOT NULL,
    aliases         TEXT,        -- JSON list
    kind            TEXT NOT NULL DEFAULT 'person'
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with _lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    # --- low level -------------------------------------------------------
    def _exec(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        with _lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur

    def _query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with _lock:
            return list(self._conn.execute(sql, params).fetchall())

    # --- captures --------------------------------------------------------
    def insert_capture(self, c: dict[str, Any]) -> None:
        self._exec(
            "INSERT INTO captures (id, created_at, source, source_type, status,"
            " processed, text, inbox_path) VALUES (?,?,?,?,?,?,?,?)",
            (c["id"], c["created_at"], c["source"], c["source_type"],
             c["status"], int(c["processed"]), c["text"], c["inbox_path"]),
        )

    def get_capture(self, cid: str) -> Optional[sqlite3.Row]:
        rows = self._query("SELECT * FROM captures WHERE id=?", (cid,))
        return rows[0] if rows else None

    def list_captures(self, status: Optional[str] = None) -> list[sqlite3.Row]:
        if status:
            return self._query(
                "SELECT * FROM captures WHERE status=? ORDER BY created_at DESC",
                (status,))
        return self._query("SELECT * FROM captures ORDER BY created_at DESC")

    def update_capture_status(self, cid: str, status: str, processed: bool,
                              decision_json: Optional[str] = None) -> None:
        if decision_json is not None:
            self._exec(
                "UPDATE captures SET status=?, processed=?, decision=? WHERE id=?",
                (status, int(processed), decision_json, cid))
        else:
            self._exec(
                "UPDATE captures SET status=?, processed=? WHERE id=?",
                (status, int(processed), cid))

    def recent_podcast_captures(self, within_seconds: int) -> list[sqlite3.Row]:
        # Used for grouping timestamped podcast notes from the same session.
        return self._query(
            "SELECT * FROM captures ORDER BY created_at DESC LIMIT 25")

    # --- audit -----------------------------------------------------------
    def insert_audit(self, a: dict[str, Any]) -> int:
        cur = self._exec(
            "INSERT INTO audit (capture_id, processed_at, action, destination,"
            " confidence, undo_available, undone, reasoning, change_made,"
            " undo_payload) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (a["capture_id"], a["processed_at"], a["action"], a.get("destination"),
             a["confidence"], int(a["undo_available"]), 0, a.get("reasoning", ""),
             a.get("change_made", ""), json.dumps(a.get("undo_payload"))),
        )
        return int(cur.lastrowid)

    def get_audit(self, aid: int) -> Optional[sqlite3.Row]:
        rows = self._query("SELECT * FROM audit WHERE id=?", (aid,))
        return rows[0] if rows else None

    def latest_audit_for_capture(self, cid: str) -> Optional[sqlite3.Row]:
        rows = self._query(
            "SELECT * FROM audit WHERE capture_id=? ORDER BY id DESC LIMIT 1",
            (cid,))
        return rows[0] if rows else None

    def list_audit(self) -> list[sqlite3.Row]:
        return self._query("SELECT * FROM audit ORDER BY id DESC")

    def mark_audit_undone(self, aid: int) -> None:
        self._exec("UPDATE audit SET undone=1, undo_available=0 WHERE id=?", (aid,))

    # --- examples --------------------------------------------------------
    def insert_example(self, e: dict[str, Any]) -> None:
        self._exec(
            "INSERT INTO examples (created_at, title, text, destination_key,"
            " note_path, note) VALUES (?,?,?,?,?,?)",
            (e["created_at"], e.get("title"), e["text"], e["destination_key"],
             e.get("note_path"), e.get("note")),
        )

    def list_examples(self) -> list[sqlite3.Row]:
        return self._query("SELECT * FROM examples ORDER BY id DESC")

    # --- entities --------------------------------------------------------
    def upsert_entity(self, e: dict[str, Any]) -> None:
        existing = self._query(
            "SELECT rowid FROM entities WHERE lower(name)=lower(?)", (e["name"],))
        if existing:
            self._exec(
                "UPDATE entities SET destination_key=?, note_path=?, aliases=?,"
                " kind=? WHERE rowid=?",
                (e["destination_key"], e["note_path"],
                 json.dumps(e.get("aliases", [])), e.get("kind", "person"),
                 existing[0]["rowid"]))
        else:
            self._exec(
                "INSERT INTO entities (name, destination_key, note_path, aliases,"
                " kind) VALUES (?,?,?,?,?)",
                (e["name"], e["destination_key"], e["note_path"],
                 json.dumps(e.get("aliases", [])), e.get("kind", "person")))

    def list_entities(self) -> list[sqlite3.Row]:
        return self._query("SELECT * FROM entities")
