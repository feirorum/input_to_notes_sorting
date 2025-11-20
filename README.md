# Semantic Sorting Lab

Experimentation repo for semantic similarity-based sorting of input snippets into a notes/knowledge base system.

## Overview

This is a web-based prototype that helps evaluate whether incoming snippets should be appended to existing notes or stored as new notes, using semantic similarity analysis.

The system uses AI embeddings to understand the meaning of text and automatically suggests the most relevant note to append to.

## Use Cases

The system can handle various snippet types:

- **Personal logs**: "Sam's shoe size is now 34" → Automatically sorts into existing shoe size notes with date
- **Project updates**: "We got the input needed from security, on the xyz project" → Adds to XYZ project note
- **Content annotations**: Notes on a podcast → Merges with timestamp and URL if matching

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Application

```bash
./run.sh
```

This will:
- Start the backend API server on `http://localhost:8000`
- Start the frontend server on `http://localhost:8080`
- Open the application in your browser

## Features

### 🔍 Semantic Similarity Analysis

Uses `paraphrase-multilingual-MiniLM-L12-v2` embeddings to compute similarity between snippets and existing notes.

### 🎯 Two Decision Modes

- **Manual Mode (A)**: View suggestions and manually select where to append
- **Auto Mode (B)**: System automatically proposes best match based on threshold

### 📝 Smart Append Logic

- **Stream notes**: Date-based log entries (e.g., "2025-11-20: New entry...")
- **Snapshot notes**: Structured content updates
- **Never notes**: Read-only reference material

### 🎨 Interactive 3-Panel UI

1. **Left Panel**: Input snippet and controls
2. **Middle Panel**: Similarity results with scores
3. **Right Panel**: Live preview with diff highlighting

## Example Notes

The system comes with 7 example notes covering different domains:

- 🚗 Vehicle maintenance log (stream mode)
- 📔 Personal diary (stream mode)
- 💻 Technical learnings (snapshot mode)
- 🏊 Swimming training log (stream mode)
- 💡 Project ideas (snapshot mode)
- 🔧 Troubleshooting guide (snapshot mode)
- 🎨 Creative concepts (never mode)

## Project Structure

```
.
├── backend/               # FastAPI server
│   ├── main.py           # API endpoints and logic
│   └── requirements.txt  # Python dependencies
├── frontend/             # Web UI
│   └── index.html        # Single-page application
├── data/
│   └── notes/           # Markdown notes with frontmatter
├── run.sh               # Convenience run script
├── SETUP.md             # Detailed setup guide
└── README.md            # This file
```

## Documentation

See [SETUP.md](SETUP.md) for:
- Detailed installation instructions
- Usage guide
- API documentation
- Troubleshooting
- Development notes

## Technology Stack

- **Backend**: Python 3.8+, FastAPI, sentence-transformers
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **ML Model**: Sentence-BERT (multilingual)
- **Data Format**: Markdown with YAML frontmatter

## Phase 1 Scope

Current implementation includes:

✅ Single embedding model
✅ Backend API with FastAPI
✅ 3-panel web interface
✅ Manual and Auto decision modes
✅ Date-based append logic for stream notes
✅ Live preview with diff highlighting
✅ 10 example snippets
✅ 7 example notes

## Future Enhancements

- Multiple embedding models comparison
- Note creation workflow
- Batch processing
- Export/import functionality
- A/B testing framework
- Obsidian plugin integration
- Podcast/YouTube integration

## License

Experimental prototype for research and evaluation purposes.

---

**Quick Links:**
- [Setup Guide](SETUP.md) - Installation and usage
- [API Docs](http://localhost:8000/docs) - Backend API (when running)
- [Frontend](http://localhost:8080) - Web UI (when running)
