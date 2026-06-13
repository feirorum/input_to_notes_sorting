"""Audit logging: structured (SQLite) + human-readable (Markdown).

Every processed item gets an entry that explains what happened and why, and
carries enough information to reverse it. The Markdown mirror lives in the vault
so the log is reviewable in Obsidian alongside the notes it describes.
"""
from __future__ import annotations

from datetime import datetime, timezone

from . import config
from .models import Decision
from .storage.db import Database


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def record(db: Database, decision: Decision, input_text: str,
           change_made: str, undo_payload: dict | None) -> int:
    processed_at = _now()
    audit_id = db.insert_audit({
        "capture_id": decision.capture_id,
        "processed_at": processed_at,
        "action": decision.decision.value,
        "destination": decision.destination,
        "confidence": decision.confidence,
        "undo_available": bool(undo_payload),
        "reasoning": decision.reason,
        "change_made": change_made,
        "undo_payload": undo_payload,
    })
    _append_markdown(decision, input_text, change_made, processed_at, audit_id)
    return audit_id


def _append_markdown(decision: Decision, input_text: str, change_made: str,
                     processed_at: str, audit_id: int) -> None:
    config.AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    log = config.AUDIT_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    entry = (
        f"\n---\n"
        f"audit_id: {audit_id}\n"
        f"capture_id: {decision.capture_id}\n"
        f"processed_at: {processed_at}\n"
        f"action: {decision.decision.value}\n"
        f"destination: {decision.destination or '-'}\n"
        f"confidence: {decision.confidence}\n"
        f"undo_available: {bool(change_made)}\n"
        f"\n**Input:** {input_text.strip()}\n\n"
        f"**Reasoning:** {decision.reason}\n\n"
        f"**Change made:** {change_made or '(none)'}\n"
    )
    with log.open("a", encoding="utf-8") as fh:
        fh.write(entry)
