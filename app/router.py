"""Service layer: capture -> classify -> route -> audit, plus undo/correct/learn.

This is the modular seam the spec asks for. Each concern (inbox storage,
classifier, markdown writer, audit logger, correction learner) is a separate
module; this file orchestrates them and owns the state transitions.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from . import audit, config
from .classifier import ClassifierContext, build_classifier
from .models import Action, Capture, CaptureStatus, CorrectIn, Decision
from .storage import inbox, vault
from .storage.db import Database


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "note"


class Service:
    def __init__(self, db: Database, classifier_kind: str | None = None):
        self.db = db
        self.classifier = build_classifier(classifier_kind)

    # --- context --------------------------------------------------------
    def _context(self) -> ClassifierContext:
        entities = [dict(r) for r in self.db.list_entities()]
        for e in entities:
            e["aliases"] = json.loads(e.get("aliases") or "[]")
        examples = [dict(r) for r in self.db.list_examples()]
        recent = [dict(r)["text"] for r in
                  self.db.recent_podcast_captures(within_seconds=0)]
        return ClassifierContext(
            entities=entities,
            examples=examples,
            note_exists=vault.note_exists,
            recent_texts=recent,
        )

    # --- capture --------------------------------------------------------
    def capture(self, text: str, source: str, source_type: str,
                created_at: str | None = None) -> Capture:
        meta = inbox.write_raw_item(text, source, source_type, created_at)
        self.db.insert_capture(meta)
        return Capture(**meta)

    # --- explain (no side effects; powers the demo) ---------------------
    def explain(self, text: str, capture_id: str = "preview") -> Decision:
        return self.classifier.classify(capture_id, text, self._context())

    def preview_target(self, decision: Decision) -> dict:
        """Return current + projected note content for the right-hand pane."""
        if not decision.destination:
            return {"path": None, "current": None, "proposed_result": None}
        current = vault.read_note(decision.destination)
        proposed_result = self._project(decision, current)
        return {"path": decision.destination, "current": current,
                "proposed_result": proposed_result}

    @staticmethod
    def _project(decision: Decision, current: str | None) -> str:
        line = decision.proposed_content.rstrip()
        if decision.decision == Action.CREATE or current is None:
            title = vault.section_title_from_path(
                decision.destination or "notes/references/new.md")
            return (f"# {title}\n\n## {decision.section or 'Notes'}\n\n{line}\n")
        section = decision.section or "Notes"
        heading = f"## {section}"
        if heading in current:
            return current.replace(heading, f"{heading}\n\n{line}", 1)
        sep = "" if current.endswith("\n") else "\n"
        return f"{current}{sep}\n{heading}\n\n{line}\n"

    # --- process --------------------------------------------------------
    def process(self, capture_id: str) -> Decision:
        row = self.db.get_capture(capture_id)
        if not row:
            raise KeyError(capture_id)
        decision = self.classifier.classify(capture_id, row["text"],
                                            self._context())
        if decision.needs_user_confirmation or decision.decision in (
                Action.ASK, Action.REVIEW):
            status = (CaptureStatus.NEEDS_REVIEW
                      if decision.decision == Action.REVIEW
                      else CaptureStatus.PENDING)
            self.db.update_capture_status(
                capture_id, status.value, processed=False,
                decision_json=decision.model_dump_json())
            audit.record(self.db, decision, row["text"],
                         change_made="", undo_payload=None)
            return decision
        return self._execute(decision, row["text"])

    def confirm(self, capture_id: str) -> Decision:
        row = self.db.get_capture(capture_id)
        if not row or not row["decision"]:
            raise KeyError(capture_id)
        decision = Decision.model_validate_json(row["decision"])
        # Confirmation makes a proposed (ask) action concrete.
        if decision.decision in (Action.ASK, Action.REVIEW):
            # nothing concrete proposed; require an explicit correction instead
            raise ValueError("This item needs a destination; use correct().")
        decision.needs_user_confirmation = False
        return self._execute(decision, row["text"])

    def _execute(self, decision: Decision, input_text: str) -> Decision:
        change_made, undo_payload = "", None
        if decision.decision == Action.APPEND:
            undo_payload = vault.append_under_section(
                decision.destination, decision.section or "Notes",
                decision.proposed_content)
            verb = "Created" if undo_payload["type"] == "created" else "Appended to"
            change_made = (f"{verb} {decision.destination} under "
                           f"'## {decision.section}': {decision.proposed_content}")
        elif decision.decision == Action.CREATE:
            title = vault.section_title_from_path(decision.destination)
            undo_payload = vault.create_note(
                decision.destination, title,
                decision.destination_key or "references",
                f"## {decision.section or 'Notes'}\n\n{decision.proposed_content}")
            change_made = f"Created {decision.destination}: {decision.proposed_content}"
        self.db.update_capture_status(
            decision.capture_id, CaptureStatus.PROCESSED.value, processed=True,
            decision_json=decision.model_dump_json())
        audit.record(self.db, decision, input_text, change_made, undo_payload)
        return decision

    # --- correction + learning -----------------------------------------
    def correct(self, capture_id: str, c: CorrectIn) -> Decision:
        row = self.db.get_capture(capture_id)
        if not row:
            raise KeyError(capture_id)
        text = row["text"]

        dest = config.DESTINATIONS_BY_KEY.get(c.destination_key)
        if not dest:
            raise ValueError(f"unknown destination_key {c.destination_key}")

        # First reverse any prior applied change for this capture.
        self._undo_latest(capture_id, silent=True)

        if c.action == Action.CREATE or (c.new_note_title and not c.note_path):
            title = c.new_note_title or vault.section_title_from_path(
                f"{dest.folder}/{_slug(text)}.md")
            note_path = c.note_path or f"{dest.folder}/{_slug(title)}.md"
            action = Action.CREATE if not vault.note_exists(note_path) else Action.APPEND
        else:
            note_path = c.note_path or f"{dest.folder}/{c.destination_key}.md"
            action = Action.APPEND if vault.note_exists(note_path) else Action.CREATE

        from .classifier import base as cbase
        decision = Decision(
            capture_id=capture_id,
            decision=action,
            confidence=1.0,
            destination=note_path,
            destination_key=c.destination_key,
            reason="User correction.",
            proposed_content=cbase._proposed_line(
                c.destination_key, text, cbase.find_timestamps(text)),
            section=cbase._section_for(c.destination_key, text),
            needs_user_confirmation=False,
        )
        result = self._execute(decision, text)

        if c.save_example:
            self._learn_example(text, c.destination_key, note_path)
        return result

    def _learn_example(self, text: str, dest_key: str, note_path: str) -> None:
        title = f"correction: {dest_key}"
        self.db.insert_example({
            "created_at": _now(),
            "title": title,
            "text": text,
            "destination_key": dest_key,
            "note_path": note_path,
            "note": "Saved from a user correction.",
        })
        self._append_example_md(title, text, dest_key, note_path)

    @staticmethod
    def _append_example_md(title: str, text: str, dest_key: str,
                           note_path: str) -> None:
        config.SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
        path = config.SYSTEM_DIR / "classification-examples.md"
        block = (
            f"\n## Example: {title}\n"
            f"- **Input:** {text.strip()}\n"
            f"- **Correct destination:** {note_path}\n"
            f"- **Category:** {dest_key}\n"
        )
        with path.open("a", encoding="utf-8") as fh:
            fh.write(block)

    # --- undo -----------------------------------------------------------
    def undo(self, capture_id: str) -> bool:
        return self._undo_latest(capture_id, silent=False)

    def _undo_latest(self, capture_id: str, silent: bool) -> bool:
        a = self.db.latest_audit_for_capture(capture_id)
        if not a or a["undone"] or not a["undo_available"]:
            return False
        payload = json.loads(a["undo_payload"] or "null")
        ok = vault.undo(payload) if payload else False
        if ok:
            self.db.mark_audit_undone(a["id"])
            self.db.update_capture_status(
                capture_id, CaptureStatus.NEW.value, processed=False)
        return ok
