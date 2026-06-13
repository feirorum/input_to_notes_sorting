"""Raw inbox storage. Core principle: never lose raw input.

Every capture is written to vault/inbox/<date>/item-NNN.md *unchanged* before
any classification or rewriting happens. The Markdown frontmatter mirrors the
spec's raw inbox item format.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .. import config


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def make_capture_id(when: datetime, seq: int) -> str:
    return f"capture-{when.strftime('%Y%m%d-%H%M%S')}-{seq:03d}"


def next_seq_for_day(day_dir: Path) -> int:
    if not day_dir.exists():
        return 1
    existing = list(day_dir.glob("item-*.md"))
    return len(existing) + 1


def write_raw_item(text: str, source: str, source_type: str,
                   created_at: str | None = None) -> dict:
    """Persist the raw capture and return its metadata dict."""
    when = datetime.now(timezone.utc).astimezone()
    if created_at:
        try:
            when = datetime.fromisoformat(created_at)
        except ValueError:
            pass
    iso = created_at or _now_iso()

    day_dir = config.INBOX_DIR / when.strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    seq = next_seq_for_day(day_dir)
    cid = make_capture_id(when, seq)
    path = day_dir / f"item-{seq:03d}.md"

    frontmatter = (
        "---\n"
        f"id: {cid}\n"
        f"created_at: {iso}\n"
        f"source: {source}\n"
        f"source_type: {source_type}\n"
        "status: new\n"
        "processed: false\n"
        "---\n\n"
    )
    path.write_text(frontmatter + text.rstrip() + "\n", encoding="utf-8")

    return {
        "id": cid,
        "created_at": iso,
        "source": source,
        "source_type": source_type,
        "status": "new",
        "processed": False,
        "text": text,
        "inbox_path": str(path.relative_to(config.VAULT_DIR)),
    }


def import_folder(folder: Path, source: str = "folder_import") -> list[dict]:
    """Import every .md/.txt file in a folder as a raw capture."""
    out = []
    for p in sorted(folder.glob("*")):
        if p.suffix.lower() in {".md", ".txt"} and p.is_file():
            out.append(write_raw_item(p.read_text(encoding="utf-8"),
                                      source, "imported_file"))
    return out
