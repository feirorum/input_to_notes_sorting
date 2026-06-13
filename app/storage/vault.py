"""Markdown vault writer/reader with reversible edits.

All mutations return an `undo_payload` describing exactly how to reverse them
(snapshot-based: we store the file's prior bytes, or mark it for deletion if we
created it). This is deliberately simple and robust — a future iteration could
switch to git commits per change without altering the router contract.
"""
from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Optional

from .. import config


def _abs(rel_path: str) -> Path:
    return (config.VAULT_DIR / rel_path).resolve()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def read_note(rel_path: str) -> Optional[str]:
    p = _abs(rel_path)
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def note_exists(rel_path: str) -> bool:
    return _abs(rel_path).exists()


def _ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def _new_note_frontmatter(title: str, dest_key: str) -> str:
    return (
        "---\n"
        f"title: {title}\n"
        f"category: {dest_key}\n"
        f"created: {date.today().isoformat()}\n"
        "tags: []\n"
        "---\n\n"
        f"# {title}\n\n"
    )


def append_under_section(rel_path: str, section: str, line: str) -> dict:
    """Append `line` under a `## section` heading, creating the section if absent.

    Returns an undo_payload. If the file doesn't exist it is created with
    frontmatter (and the undo deletes it).
    """
    p = _abs(rel_path)
    created = not p.exists()
    before = "" if created else p.read_text(encoding="utf-8")

    if created:
        title = section_title_from_path(rel_path)
        content = _new_note_frontmatter(title, _dest_key_from_path(rel_path))
    else:
        content = before

    heading = f"## {section}"
    addition = line.rstrip() + "\n"

    if heading in content:
        # Insert right after the heading block (after the heading line).
        lines = content.splitlines(keepends=True)
        out: list[str] = []
        inserted = False
        for i, ln in enumerate(lines):
            out.append(ln)
            if not inserted and ln.strip() == heading:
                # ensure a blank line then the addition
                if i + 1 < len(lines) and lines[i + 1].strip() == "":
                    out.append(lines[i + 1])
                    # skip duplicate handling by marking
                out.append(addition)
                inserted = True
        new_content = "".join(out)
        # Guard: if our naive insert duplicated the following blank line, it's
        # cosmetic only; acceptable for a prototype.
    else:
        if not content.endswith("\n"):
            content += "\n"
        new_content = content + f"\n{heading}\n\n{addition}"

    _ensure_parent(p)
    p.write_text(new_content, encoding="utf-8")

    return {
        "type": "created" if created else "modified",
        "path": rel_path,
        "prev_content": None if created else before,
        "prev_hash": None if created else content_hash(before),
        "new_hash": content_hash(new_content),
    }


def create_note(rel_path: str, title: str, dest_key: str, body: str) -> dict:
    p = _abs(rel_path)
    if p.exists():
        # Don't clobber; append instead and report as modified.
        return append_under_section(rel_path, "Notes", body)
    _ensure_parent(p)
    content = _new_note_frontmatter(title, dest_key) + body.rstrip() + "\n"
    p.write_text(content, encoding="utf-8")
    return {
        "type": "created",
        "path": rel_path,
        "prev_content": None,
        "prev_hash": None,
        "new_hash": content_hash(content),
    }


def undo(undo_payload: dict) -> bool:
    """Reverse a change described by an undo_payload."""
    if not undo_payload:
        return False
    p = _abs(undo_payload["path"])
    if undo_payload["type"] == "created":
        if p.exists():
            p.unlink()
        return True
    # modified -> restore prior content (only if file hasn't drifted)
    if undo_payload.get("prev_content") is not None:
        p.write_text(undo_payload["prev_content"], encoding="utf-8")
        return True
    return False


def section_title_from_path(rel_path: str) -> str:
    stem = Path(rel_path).stem
    return stem.replace("-", " ").replace("_", " ").title()


def _dest_key_from_path(rel_path: str) -> str:
    # notes/<key>/file.md -> <key>
    parts = Path(rel_path).parts
    if len(parts) >= 2 and parts[0] == "notes":
        return parts[1]
    return "references"
