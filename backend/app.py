from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path

from models import Note, Snippet, Match, MatchResult
from matchers import (
    KeywordMatcher,
    StructureMatcher,
    EntityMatcher,
    ContextMatcher,
    ProjectMatcher
)
from scoring import ScoreAggregator
from inserters import AppendInserter, MergeInserter
from action_log import action_log, ActionLogEntry

# Initialize FastAPI app
app = FastAPI(title="Input to Notes Sorting API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load test data
def load_notes() -> List[Note]:
    """Load notes from test data"""
    notes_file = Path(__file__).parent / "test_data" / "notes.json"
    with open(notes_file) as f:
        notes_data = json.load(f)
    return [Note(**note_data) for note_data in notes_data]

def load_snippets() -> List[Snippet]:
    """Load snippets from test data"""
    snippets_file = Path(__file__).parent / "test_data" / "snippets.json"
    with open(snippets_file) as f:
        snippets_data = json.load(f)
    return [Snippet(**snippet_data) for snippet_data in snippets_data]

# Global data storage (in production, use a database)
notes_db = load_notes()
snippets_db = load_snippets()

# Initialize matchers
matchers = [
    KeywordMatcher(),
    StructureMatcher(),
    EntityMatcher(),
    ContextMatcher(),
    ProjectMatcher()
]

# Initialize score aggregator
aggregator = ScoreAggregator(matchers)

# Initialize inserters
inserters = {
    "APPEND": AppendInserter(),
    "MERGE": MergeInserter(),
    "LINK": AppendInserter(),  # For demo, use append
}


# API Models
class MatchRequest(BaseModel):
    """Request to match a snippet"""
    snippet: Snippet


class ApplyMatchRequest(BaseModel):
    """Request to apply a match"""
    snippet: Snippet
    match: Match
    was_manual_review: bool = False


# API Endpoints

@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "Input to Notes Sorting API", "version": "1.0.0"}


@app.get("/notes", response_model=List[Note])
def get_notes():
    """Get all notes"""
    return notes_db


@app.get("/notes/{note_id}", response_model=Note)
def get_note(note_id: str):
    """Get a specific note"""
    for note in notes_db:
        if note.id == note_id:
            return note
    raise HTTPException(status_code=404, detail="Note not found")


@app.get("/snippets", response_model=List[Snippet])
def get_snippets():
    """Get all example snippets"""
    return snippets_db


@app.get("/snippets/{snippet_id}", response_model=Snippet)
def get_snippet(snippet_id: str):
    """Get a specific snippet"""
    for snippet in snippets_db:
        if snippet.id == snippet_id:
            return snippet
    raise HTTPException(status_code=404, detail="Snippet not found")


@app.post("/match", response_model=MatchResult)
def match_snippet(request: MatchRequest):
    """Match a snippet against all notes

    Returns ranked list of matches with scores from all matchers
    """
    snippet = request.snippet
    result = aggregator.aggregate_scores(snippet, notes_db)
    return result


@app.post("/apply", response_model=ActionLogEntry)
def apply_match(request: ApplyMatchRequest):
    """Apply a match (insert snippet into note)

    This is for demo purposes - shows what would happen
    In production, would actually modify the note
    """
    snippet = request.snippet
    match = request.match

    # Find the note
    note = None
    for n in notes_db:
        if n.id == match.note_id:
            note = n
            break

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Get appropriate inserter
    inserter = inserters.get(match.insertion_strategy.value)
    if not inserter:
        inserter = inserters["APPEND"]

    # Apply insertion (get modified content and undo info)
    modified_content, undo_info = inserter.insert(snippet, note)

    # In demo mode, we don't actually modify the note
    # Just log the action
    log_entry = action_log.add_entry(
        snippet=snippet,
        match=match,
        undo_info=undo_info,
        was_manual_review=request.was_manual_review
    )

    return log_entry


@app.get("/history", response_model=List[ActionLogEntry])
def get_history(limit: int = 20):
    """Get action history"""
    return action_log.get_recent(limit)


@app.get("/history/{action_id}", response_model=ActionLogEntry)
def get_action(action_id: str):
    """Get a specific action"""
    entry = action_log.get_by_id(action_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Action not found")
    return entry


@app.post("/undo/{action_id}")
def undo_action(action_id: str):
    """Undo a specific action

    For demo purposes - in production would restore note content
    """
    entry = action_log.get_by_id(action_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Action not found")

    # In production, would use undo_info to restore note
    return {
        "status": "success",
        "message": f"Action {action_id} would be undone",
        "undo_info": entry.undo_info
    }


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "notes_count": len(notes_db),
        "snippets_count": len(snippets_db),
        "matchers_count": len(matchers),
        "history_count": len(action_log.entries)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
