# Semantic Sorting Lab - Setup Guide

## Overview

This is a prototype web-based lab for testing semantic similarity between incoming snippets and existing notes (markdown). The system helps evaluate if a snippet should be appended to an existing note or stored as a new note.

## Architecture

- **Backend**: Python FastAPI with sentence-transformers
- **Frontend**: Single-page HTML/CSS/JavaScript application
- **Embedding Model**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Data**: Markdown files with YAML frontmatter

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Web browser (Chrome, Firefox, Safari, or Edge)

## Installation

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note**: First run will download the embedding model (~400MB). This may take a few minutes depending on your internet connection.

### 2. Verify Installation

Check that all packages are installed:

```bash
python -c "import fastapi, sentence_transformers; print('All dependencies installed!')"
```

## Running the Application

### Option 1: Using the Run Script (Recommended)

```bash
./run.sh
```

This will:
1. Start the backend API server on `http://localhost:8000`
2. Open the frontend in your default browser

### Option 2: Manual Start

**Terminal 1 - Start Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Serve Frontend:**
```bash
cd frontend
python -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

## Using the Application

### Panel 1: Snippet Input

1. **Enter a snippet** manually in the textarea, OR
2. **Click an example** from the list to auto-load and analyze

**Controls:**
- **Decision Mode**:
  - `Manual (A)`: Shows suggestions but requires manual selection
  - `Auto-baseline (B)`: Automatically proposes best match above threshold
- **Score Threshold**: Minimum similarity score for auto-append (default: 0.80)
- **Analyze Snippet**: Click to compute similarities (or press Ctrl+Enter in textarea)

### Panel 2: Similarity Results

- View top 10 similar notes ranked by score
- **Score**: Cosine similarity (0-1, higher = more similar)
- **Mode**: Note's append behavior
  - `stream`: Can append with date-based entries
  - `snapshot`: Can append but structured differently
  - `never`: Cannot append, read-only
- In **Auto mode**: Shows which note would be auto-selected
- In **Manual mode**: Top match above threshold is highlighted (ghost suggestion)

### Panel 3: Note Preview

- Click any result row to preview the note
- See where the snippet would be inserted (highlighted in green)
- **Actions**:
  - **Append to this note**: Save snippet to selected note
  - **Create new note**: (Placeholder in Phase 1)

## Project Structure

```
input_to_notes_sorting/
├── backend/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── frontend/
│   └── index.html          # Single-page web UI
├── data/
│   └── notes/              # Markdown notes with frontmatter
│       ├── vw_t4_logg.md
│       ├── dagbok_2025.md
│       ├── lardomar_copilot.md
│       └── ...
├── SETUP.md                # This file
└── run.sh                  # Convenience run script
```

## Note Format

Notes are markdown files with YAML frontmatter:

```markdown
---
id: unique_note_id
title: "Human Readable Title"
append_mode: "stream"      # "stream" | "snapshot" | "never"
folder: "Category/Path"
---

2025-11-01: First entry...
2025-11-15: Another entry...
```

### Append Modes

- **stream**: Log-style notes with date entries (YYYY-MM-DD:). New snippets append after last date.
- **snapshot**: Structured notes that can be updated but don't follow date format
- **never**: Read-only notes, no appending allowed

## API Endpoints

The backend provides these endpoints:

- `GET /` - Health check
- `GET /notes` - List all notes
- `GET /notes/{note_id}` - Get specific note
- `POST /analyze` - Analyze snippet similarity
- `POST /preview-append` - Preview append operation
- `POST /append` - Actually append snippet to note

API docs available at: `http://localhost:8000/docs`

## Troubleshooting

### Backend won't start

- Ensure Python 3.8+ is installed: `python --version`
- Check all dependencies are installed: `pip install -r backend/requirements.txt`
- Port 8000 might be in use: `lsof -i :8000` (kill process if needed)

### Frontend shows CORS errors

- Ensure backend is running on `http://localhost:8000`
- Check browser console for specific errors
- Try a different browser

### Model download fails

- Check internet connection
- Manually download: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"`
- Model will be cached in `~/.cache/torch/sentence_transformers/`

### No results returned

- Check that notes exist in `data/notes/` directory
- Verify notes have proper frontmatter format
- Check backend logs for errors

## Development Notes

### Adding New Notes

1. Create a new `.md` file in `data/notes/`
2. Include proper frontmatter (see format above)
3. Restart backend to load new notes

### Modifying Frontend

The frontend is a single HTML file with embedded CSS and JavaScript. Edit `frontend/index.html` and refresh your browser.

### Modifying Backend

Edit `backend/main.py` and restart the backend server.

## Phase 1 Limitations

Current prototype has these known limitations:

- Single embedding model only (no switching)
- "Create new note" button is a placeholder
- No authentication or multi-user support
- In-memory note loading (no database)
- Simple date-based append logic only
- No undo functionality

## Future Enhancements (Phase 2+)

- Multiple embedding model comparison
- Advanced append strategies
- Note creation UI
- Batch processing
- Export results/metrics
- A/B testing framework
- Integration with Obsidian

## License

Experimental/Research prototype - not for production use.
