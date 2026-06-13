import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def service(monkeypatch, tmp_path):
    """A Service wired to a throwaway vault + db, seeded like the app."""
    vault = tmp_path / "vault"
    (vault / "notes" / "family").mkdir(parents=True)
    (vault / "system").mkdir(parents=True)
    (vault / "audit-log").mkdir(parents=True)
    (vault / "inbox").mkdir(parents=True)

    # Seed the Flora note so append-to-existing works.
    (vault / "notes" / "family" / "flora.md").write_text(
        "---\ntitle: Flora\ncategory: family\n---\n\n# Flora\n\n"
        "## Clothing and sizes\n\n2025-09-01: Shoe size 33.\n",
        encoding="utf-8")

    from app import config
    monkeypatch.setattr(config, "VAULT_DIR", vault)
    monkeypatch.setattr(config, "INBOX_DIR", vault / "inbox")
    monkeypatch.setattr(config, "NOTES_DIR", vault / "notes")
    monkeypatch.setattr(config, "SYSTEM_DIR", vault / "system")
    monkeypatch.setattr(config, "AUDIT_DIR", vault / "audit-log")

    from app.storage.db import Database
    db = Database(tmp_path / "t.db")
    # seed entities + examples
    for e in config.ENTITIES:
        db.upsert_entity({"name": e.name, "destination_key": e.destination_key,
                          "note_path": e.note_path, "aliases": list(e.aliases),
                          "kind": e.kind})
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    for ex in config.SEED_EXAMPLES:
        db.insert_example({"created_at": now, **ex})

    from app.router import Service
    return Service(db, classifier_kind="rules")
