"""
Semantic Sorting Lab - Backend API
FastAPI application for computing similarity between snippets and notes
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import frontmatter

# Initialize FastAPI app
app = FastAPI(title="Semantic Sorting Lab API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load embedding model
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
print(f"Loading embedding model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)
print("Model loaded successfully!")

# Notes directory
NOTES_DIR = Path(__file__).parent.parent / "data" / "notes"


# Pydantic models
class SnippetRequest(BaseModel):
    snippet: str
    threshold: float = 0.80
    mode: str = "manual"  # "manual" or "auto"
    top_k: int = 10


class SimilarityResult(BaseModel):
    rank: int
    note_id: str
    title: str
    score: float
    append_mode: str
    folder: str
    auto_suggestion: Optional[str] = None


class AnalysisResponse(BaseModel):
    snippet: str
    results: List[SimilarityResult]
    auto_proposal: Optional[Dict[str, any]] = None


class AppendRequest(BaseModel):
    note_id: str
    snippet: str


class Note:
    """Represents a markdown note with frontmatter"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.load()

    def load(self):
        """Load note from file"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            self.metadata = post.metadata
            self.content = post.content

        # Extract metadata fields
        self.id = self.metadata.get('id', self.file_path.stem)
        self.title = self.metadata.get('title', self.file_path.stem)
        self.append_mode = self.metadata.get('append_mode', 'never')
        self.folder = self.metadata.get('folder', 'General')

    def get_full_text(self) -> str:
        """Get full text for embedding (title + content)"""
        return f"{self.title}\n\n{self.content}"

    def find_append_location(self) -> Optional[int]:
        """
        Find the position to append new content.
        For 'stream' mode: find last date match (YYYY-MM-DD:)
        Returns character position, or None if not found
        """
        if self.append_mode != "stream":
            return None

        # Find all date patterns YYYY-MM-DD:
        date_pattern = r'\d{4}-\d{2}-\d{2}:'
        matches = list(re.finditer(date_pattern, self.content))

        if not matches:
            return None

        # Get last match and find end of that line
        last_match = matches[-1]
        line_end = self.content.find('\n', last_match.end())

        if line_end == -1:
            # Last line, append at end
            return len(self.content)

        return line_end + 1

    def preview_append(self, snippet: str) -> str:
        """
        Preview what the note would look like with snippet appended
        """
        if self.append_mode == "never":
            return self.content

        append_pos = self.find_append_location()

        if append_pos is None:
            # Append at end if no date pattern found
            today = datetime.now().strftime("%Y-%m-%d")
            new_entry = f"\n{today}: {snippet}"
            return self.content + new_entry

        # Insert at found position
        today = datetime.now().strftime("%Y-%m-%d")
        new_entry = f"{today}: {snippet}\n"

        preview = self.content[:append_pos] + new_entry + self.content[append_pos:]
        return preview

    def append_snippet(self, snippet: str):
        """
        Actually append snippet to the note file
        """
        new_content = self.preview_append(snippet)
        self.content = new_content

        # Write back to file
        post = frontmatter.Post(self.content, **self.metadata)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))


def load_all_notes() -> List[Note]:
    """Load all markdown notes from data directory"""
    notes = []

    if not NOTES_DIR.exists():
        print(f"Notes directory not found: {NOTES_DIR}")
        return notes

    for note_file in NOTES_DIR.glob("**/*.md"):
        try:
            note = Note(note_file)
            notes.append(note)
        except Exception as e:
            print(f"Error loading note {note_file}: {e}")

    return notes


def compute_similarity(snippet: str, notes: List[Note], top_k: int = 10) -> List[tuple]:
    """
    Compute cosine similarity between snippet and all notes
    Returns list of (note, score) tuples, sorted by score descending
    """
    if not notes:
        return []

    # Encode snippet
    snippet_embedding = model.encode([snippet])[0]

    # Encode all notes
    note_texts = [note.get_full_text() for note in notes]
    note_embeddings = model.encode(note_texts)

    # Compute cosine similarities
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity([snippet_embedding], note_embeddings)[0]

    # Pair notes with scores and sort
    results = list(zip(notes, similarities))
    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_k]


@app.get("/")
async def root():
    return {"message": "Semantic Sorting Lab API", "status": "running"}


@app.get("/notes")
async def get_notes():
    """Get list of all available notes"""
    notes = load_all_notes()
    return {
        "count": len(notes),
        "notes": [
            {
                "id": note.id,
                "title": note.title,
                "append_mode": note.append_mode,
                "folder": note.folder
            }
            for note in notes
        ]
    }


@app.get("/notes/{note_id}")
async def get_note(note_id: str):
    """Get full content of a specific note"""
    notes = load_all_notes()

    for note in notes:
        if note.id == note_id:
            return {
                "id": note.id,
                "title": note.title,
                "append_mode": note.append_mode,
                "folder": note.folder,
                "content": note.content
            }

    raise HTTPException(status_code=404, detail="Note not found")


@app.post("/analyze")
async def analyze_snippet(request: SnippetRequest) -> AnalysisResponse:
    """
    Analyze snippet and find similar notes
    """
    snippet = request.snippet.strip()

    if not snippet:
        raise HTTPException(status_code=400, detail="Snippet cannot be empty")

    # Load notes and compute similarities
    notes = load_all_notes()

    if not notes:
        raise HTTPException(status_code=500, detail="No notes found in database")

    similarities = compute_similarity(snippet, notes, request.top_k)

    # Build results
    results = []
    auto_proposal = None
    best_auto_target = None

    for rank, (note, score) in enumerate(similarities, 1):
        # Determine auto suggestion
        auto_suggestion = None
        if request.mode == "auto":
            if score >= request.threshold and note.append_mode == "stream":
                if best_auto_target is None:
                    best_auto_target = note
                    auto_suggestion = "🔁 Append (auto)"

        results.append(SimilarityResult(
            rank=rank,
            note_id=note.id,
            title=note.title,
            score=round(score, 3),
            append_mode=note.append_mode,
            folder=note.folder,
            auto_suggestion=auto_suggestion
        ))

    # Set auto proposal if found
    if request.mode == "auto" and best_auto_target:
        auto_proposal = {
            "action": "append",
            "target_note_id": best_auto_target.id,
            "target_title": best_auto_target.title,
            "score": round(similarities[0][1], 3),
            "reason": f"score = {round(similarities[0][1], 3)} ≥ threshold ({request.threshold}) ∧ append_mode = stream"
        }

    return AnalysisResponse(
        snippet=snippet,
        results=results,
        auto_proposal=auto_proposal
    )


@app.post("/preview-append")
async def preview_append(request: AppendRequest):
    """
    Preview what note would look like with snippet appended
    """
    notes = load_all_notes()

    for note in notes:
        if note.id == request.note_id:
            preview = note.preview_append(request.snippet)

            # Find where the new content is
            append_pos = note.find_append_location()

            return {
                "note_id": note.id,
                "title": note.title,
                "original_content": note.content,
                "preview_content": preview,
                "append_position": append_pos
            }

    raise HTTPException(status_code=404, detail="Note not found")


@app.post("/append")
async def append_to_note(request: AppendRequest):
    """
    Actually append snippet to note
    """
    notes = load_all_notes()

    for note in notes:
        if note.id == request.note_id:
            try:
                note.append_snippet(request.snippet)
                return {
                    "success": True,
                    "message": f"Snippet appended to {note.title}",
                    "note_id": note.id
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Error appending: {str(e)}")

    raise HTTPException(status_code=404, detail="Note not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
