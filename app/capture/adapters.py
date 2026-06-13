"""Capture adapters.

V1 ships three: the web form / POST endpoint (handled in main.py), and folder
import (here). The adapter boundary is intentionally thin so email/webhook/Keep
adapters can be added later without touching the classifier or router.
"""
from __future__ import annotations

from pathlib import Path

from ..router import Service


def import_folder(service: Service, folder: str) -> list[str]:
    """Import a folder of .md/.txt files as raw captures. Returns capture ids."""
    p = Path(folder).expanduser().resolve()
    if not p.is_dir():
        raise NotADirectoryError(folder)
    ids = []
    for f in sorted(p.glob("*")):
        if f.suffix.lower() in {".md", ".txt"} and f.is_file():
            cap = service.capture(f.read_text(encoding="utf-8"),
                                  source="folder_import",
                                  source_type="imported_file")
            ids.append(cap.id)
    return ids
