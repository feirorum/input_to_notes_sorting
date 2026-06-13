"""FastAPI app: capture endpoints, processing, review/undo/correct, and demo UI."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import config
from .capture import adapters
from .models import CaptureIn, CorrectIn
from .router import Service
from .storage.db import Database

BASE = Path(__file__).parent

app = FastAPI(title="Capture Inbox -> Obsidian Sorter")
templates = Jinja2Templates(directory=str(BASE / "web" / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE / "web" / "static")),
          name="static")

db = Database(config.DB_PATH)
service = Service(db)


# --- seeding ---------------------------------------------------------------
def seed() -> None:
    for d in (config.INBOX_DIR, config.NOTES_DIR, config.SYSTEM_DIR,
              config.AUDIT_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not db.list_entities():
        for e in config.ENTITIES:
            db.upsert_entity({
                "name": e.name, "destination_key": e.destination_key,
                "note_path": e.note_path, "aliases": list(e.aliases),
                "kind": e.kind,
            })
    if not db.list_examples():
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        for ex in config.SEED_EXAMPLES:
            db.insert_example({"created_at": now, "title": ex["title"],
                               "text": ex["text"],
                               "destination_key": ex["destination_key"],
                               "note_path": ex["note_path"],
                               "note": ex["note"]})


seed()


# --- API: capture ----------------------------------------------------------
@app.post("/capture")
def capture(item: CaptureIn):
    cap = service.capture(item.text, item.source, item.source_type,
                          item.created_at)
    return cap.model_dump()


@app.get("/inbox")
def inbox():
    rows = db.list_captures(status="new")
    return [dict(r) for r in rows]


@app.post("/import")
def import_folder(payload: dict):
    folder = payload.get("folder")
    if not folder:
        raise HTTPException(400, "folder required")
    try:
        ids = adapters.import_folder(service, folder)
    except (NotADirectoryError, FileNotFoundError) as exc:
        raise HTTPException(400, str(exc))
    return {"imported": ids}


# --- API: process / confirm / correct / undo -------------------------------
@app.post("/process/{capture_id}")
def process(capture_id: str):
    try:
        decision = service.process(capture_id)
    except KeyError:
        raise HTTPException(404, "capture not found")
    return _decision_with_preview(decision)


@app.post("/confirm/{capture_id}")
def confirm(capture_id: str):
    try:
        decision = service.confirm(capture_id)
    except KeyError:
        raise HTTPException(404, "capture not found")
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return _decision_with_preview(decision)


@app.post("/correct/{capture_id}")
def correct(capture_id: str, c: CorrectIn):
    try:
        decision = service.correct(capture_id, c)
    except KeyError:
        raise HTTPException(404, "capture not found")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return _decision_with_preview(decision)


@app.post("/undo/{capture_id}")
def undo(capture_id: str):
    ok = service.undo(capture_id)
    if not ok:
        raise HTTPException(409, "nothing to undo")
    return {"undone": True, "capture_id": capture_id}


# --- API: review / audit / explain -----------------------------------------
@app.get("/review")
def review():
    out = []
    for status in ("pending", "needs_review"):
        for r in db.list_captures(status=status):
            d = dict(r)
            if d.get("decision"):
                d["decision"] = json.loads(d["decision"])
            out.append(d)
    return out


@app.get("/processed")
def processed():
    return [dict(r) for r in db.list_captures(status="processed")]


@app.get("/audit")
def audit_log():
    return [dict(r) for r in db.list_audit()]


@app.post("/explain")
def explain(payload: dict):
    """Score a note without committing — drives the demo's three panes."""
    text = (payload or {}).get("text", "").strip()
    if not text:
        raise HTTPException(400, "text required")
    decision = service.explain(text)
    return _decision_with_preview(decision)


@app.get("/note")
def note(path: str):
    from .storage import vault
    content = vault.read_note(path)
    if content is None:
        raise HTTPException(404, "note not found")
    return {"path": path, "content": content}


@app.get("/config")
def get_config():
    return {
        "classifier": service.classifier.name
        if hasattr(service.classifier, "name") else config.settings.classifier,
        "destinations": [{"key": d.key, "label": d.label, "folder": d.folder}
                         for d in config.DESTINATIONS],
        "entities": [dict(r) for r in db.list_entities()],
        "thresholds": {
            "low_confidence": config.settings.low_confidence,
            "auto_confidence": config.settings.auto_confidence,
            "ambiguity_margin": config.settings.ambiguity_margin,
        },
    }


# --- UI --------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    examples = [
        "Flora's feet are now size 34.",
        "We got the input needed from security on the XYZ project.",
        "Practical AI podcast 17:43 — context windows explained clearly.",
        "Practical AI 17:55 — idea for Copilot champions session.",
        "Remind me to buy batteries and milk tomorrow.",
        "My bank account password is hunter2.",
        "Read this great paper on RAG embeddings for agents.",
        "Did a 5k run this morning, felt strong.",
    ]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "examples": examples,
        "destinations": config.DESTINATIONS,
        "classifier": getattr(service.classifier, "name",
                              config.settings.classifier),
    })


# --- helpers ---------------------------------------------------------------
def _decision_with_preview(decision):
    data = decision.model_dump()
    data["preview"] = service.preview_target(decision)
    return JSONResponse(data)
