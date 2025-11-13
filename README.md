# Input to Notes Sorting - POC Demo

Smart routing system for personal knowledge bases. Automatically sorts input snippets to the right notes using multiple matching strategies.

## 🎯 Overview

This POC demonstrates an intelligent note sorting system that:
- Analyzes input snippets using 5 different matchers (Keyword, Structure, Entity, Context, Project)
- Shows transparent decision-making with visual score breakdowns
- Supports time-based matching for podcast/video notes (5min before → 20min after with gradual scoring)
- Handles ambiguous matches with manual review queue
- Tracks all sorting actions with undo capability
- Provides real-time preview of where snippets will be inserted

## 🏗️ Architecture

```
├── backend/                 # Python FastAPI backend
│   ├── models/             # Data models (Note, Snippet, Match)
│   ├── matchers/           # 5 matcher implementations
│   ├── inserters/          # Insertion strategies (APPEND, MERGE, LINK)
│   ├── scoring/            # Score aggregation logic
│   ├── action_log.py       # Sorting history with undo
│   ├── app.py              # FastAPI application
│   └── test_data/          # Mock notes and snippets
└── frontend/                # HTML/CSS/JS demo interface
    ├── index.html          # 4-pane layout
    ├── styles.css          # Responsive styling
    └── app.js              # API integration & UI logic
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Modern web browser

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Backend Server

```bash
cd backend
python app.py
```

The API will be available at `http://localhost:8000`

### 3. Open Frontend

Simply open `frontend/index.html` in your web browser, or serve it:

```bash
cd frontend
python -m http.server 8080
```

Then visit `http://localhost:8080`

## 🎨 Demo Interface

### Four Panes:

1. **Input Examples (Left)**
   - Pre-loaded snippets covering different scenarios
   - Custom input with editable timestamps
   - Select any snippet to trigger matching

2. **Matching Analysis (Top Middle)**
   - Real-time score visualization
   - All 5 matchers shown with score bars
   - Confidence levels (High/Medium/Low)
   - Human-readable reasoning

3. **Preview (Bottom Middle)**
   - See exactly where snippet will be inserted
   - Highlighted additions
   - Full note context

4. **Sorting History (Right)**
   - One-line summaries of all actions
   - Manual review indicators
   - Timestamp tracking

## 🧪 Test Scenarios

### Scenario 1: Shoe Size Update
**Input:** "Sam's shoe size is now 34"

**Expected Behavior:**
- StructureMatcher: High score (0.85+) - detects "Name: Number" pattern
- KeywordMatcher: High score (0.90+) - finds "shoe size" in Family Info note
- Routes to: "Family Info > Shoe Sizes" section
- Inserts as: "- Sam: 34 (2025-01-13)"

### Scenario 2: Project Update
**Input:** "We got the input needed from security, on the xyz project"

**Expected Behavior:**
- ProjectMatcher: Very high score (0.90+) - detects "XYZ project"
- EntityMatcher: High score - matches "security" entity
- Routes to: "Project XYZ - Customer Portal"
- Inserts in: Recent Updates section

### Scenario 3: Podcast Note with Timestamp
**Input:** "[15:23] Interesting point about CAP theorem..."

**Metadata:**
- URL: `https://softwareengineeringdaily.com/episode-442`
- Media duration: 58 minutes
- Listen time: 10:00 AM

**Expected Behavior:**
- ContextMatcher: Perfect score (1.0) - URL match + timestamp within playback window
- StructureMatcher: High score (0.85) - detects timestamped note pattern
- Routes to: Existing podcast note with matching URL
- Inserts as: "[15:23] Interesting point about CAP theorem..."

### Scenario 4: Out-of-Range Podcast Note
**Input:** "[62:30] Final thoughts..." (podcast is only 58 minutes)

**Expected Behavior:**
- ContextMatcher: Reduced score (0.25) - timestamp beyond media duration
- System flags as low confidence
- May trigger manual review

### Scenario 5: Ambiguous Match
**Input:** "Interesting article about distributed systems"

**Expected Behavior:**
- Multiple matches with similar scores:
  - "Reading List" (0.72)
  - "Podcast: Distributed Systems" (0.70)
  - "Research: ML Optimization" (0.65)
- Triggers manual review modal
- User selects appropriate destination

## 🔧 Matcher Details

### KeywordMatcher
- Extracts keywords and 2-3 word phrases
- Filters stop words
- Weighted scoring: exact phrases (0.4), phrases (0.3), keywords (0.1)

### StructureMatcher
- Detects patterns: lists, timestamps, code blocks, tasks, expenses
- Matches snippet structure to note structures
- Special handling for name-value pairs

### EntityMatcher
- Extracts: people names, project references, technical terms
- Uses Jaccard similarity for overlap
- Title matches heavily weighted

### ContextMatcher (Time-Based)
- URL matching for media sources
- Time window: 5 minutes before → during → 20 minutes after
- Gradual scoring:
  - 5min before: 0.3 → 1.0 (linear increase)
  - During playback: 1.0 (full score)
  - 20min after: 1.0 → 0.5 (linear decrease)
- Validates timestamp within media duration

### ProjectMatcher
- Pattern recognition: "XYZ project", "Project ABC", etc.
- Title matching prioritized
- Handles capitalized identifiers

## 📊 Scoring System

### Weighted Aggregation
```python
Default weights:
- Keyword: 0.25
- Structure: 0.20
- Entity: 0.20
- Context: 0.25
- Project: 0.10

Media snippet weights (adjusted):
- Context: 0.40  # Higher priority for media
- Keyword: 0.20
- Others: Lower
```

### Confidence Levels
- **High (≥0.8):** Auto-apply recommended
- **Medium (0.5-0.79):** Review suggested
- **Low (<0.5):** Manual review required

### Manual Review Triggers
1. Top match < 0.8 confidence
2. Multiple matches within 0.1 of each other
3. No matches found

## 🔄 Action Log & Undo

Every sort action records:
- Original snippet content
- Selected match (note, score, strategy)
- Timestamp
- Undo information (original note content)
- Manual review flag

History shows:
- One-line summaries (emoji + snippet → note)
- Chronological order (newest first)
- Manual review indicators

Undo functionality:
- `/undo/{action_id}` endpoint
- Restores original note content
- For demo: shows undo info, doesn't modify

## 🌐 API Endpoints

### GET /snippets
Returns all example snippets

### GET /notes
Returns all mock notes

### POST /match
```json
{
  "snippet": {
    "content": "Sam's shoe size is now 34",
    "source": "manual",
    "timestamp": "2025-01-13T15:30:00Z",
    "metadata": {}
  }
}
```

Returns: `MatchResult` with ranked matches and scores

### POST /apply
Apply a match and log the action

### GET /history
Get sorting action history

### POST /undo/{action_id}
Undo a specific action

### GET /health
Health check with stats

## 🎯 Success Metrics (Demo)

- ✅ 15 mock notes across diverse categories
- ✅ 15 test snippets covering all scenarios
- ✅ 5 matchers implemented and working
- ✅ Time-based gradual scoring (5min before, 20min after)
- ✅ 4-pane visual interface
- ✅ Manual review queue for ambiguous matches
- ✅ Action history with one-line summaries
- ✅ Preview with insertion point highlighting
- ✅ Editable timestamps for testing

## 🚧 Future Enhancements

1. **Real Podcast/YouTube Integration**
   - Fetch metadata from URLs
   - Auto-detect media duration
   - Episode ID matching across platforms

2. **Machine Learning**
   - Train on user corrections
   - Learn category preferences
   - Improve over time

3. **Advanced Insertion**
   - Smart section detection
   - Semantic merging
   - Conflict resolution

4. **Multi-User Support**
   - Personal note collections
   - Shared team knowledge bases
   - Permission management

5. **Real Database**
   - Persistent storage
   - Actual note modification
   - Full undo/redo stack

## 📝 Notes

- **Demo Mode:** Frontend doesn't actually modify notes, just shows previews
- **Mock Data:** All notes and snippets are examples in `backend/test_data/`
- **CORS:** Enabled for all origins (restrict in production)
- **Timestamps:** Editable in UI for testing time-based matching

## 🐛 Troubleshooting

**Backend won't start:**
```bash
pip install --upgrade fastapi uvicorn pydantic python-dateutil
```

**Frontend can't connect:**
- Check backend is running on port 8000
- Look for CORS errors in browser console
- Verify API_BASE_URL in `app.js`

**Matches not showing:**
- Check browser console for errors
- Verify test data loaded: `http://localhost:8000/health`
- Try a simple example first (shoe size)

## 👤 Development

Built as POC to demonstrate:
- Transparent AI decision-making (show the scores!)
- Multi-strategy matching (no single approach works for all)
- Time-context awareness (podcast/video integration)
- User control (manual review for ambiguity)
- Undo capability (safety net for automation)

Ready for production with:
- Real database (PostgreSQL/MongoDB)
- ML models (fine-tuned embeddings)
- Authentication
- Real-time sync
- Mobile apps

---

**Try it now!** Start the backend, open the frontend, and click on any example snippet to see the magic happen. 🎩✨
