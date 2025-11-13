# 🚀 Quick Start Guide

Get the POC demo running in 3 simple steps!

## Step 1: Start the Backend (Terminal 1)

```bash
cd backend
pip install -r requirements.txt
python app.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Keep this terminal open! ✅

## Step 2: Open the Frontend

**Option A: Direct file open**
- Simply open `frontend/index.html` in your browser
- Most browsers allow this for local development

**Option B: Simple HTTP server** (if Option A doesn't work)
```bash
# In a new terminal (Terminal 2)
cd frontend
python -m http.server 8080
```

Then visit: `http://localhost:8080`

## Step 3: Try the Demo! 🎉

### Example 1: Shoe Size Update
1. Click on the first snippet: **"Sam's shoe size is now 34"**
2. Watch the matching analysis appear
3. See how StructureMatcher and KeywordMatcher both score high
4. Preview shows it will be added to "Family Info > Shoe Sizes"
5. Click **"Apply This Match"**
6. Check the Sorting History on the right!

### Example 2: Podcast Note
1. Click on the snippet with **"[15:23] Interesting point about CAP theorem"**
2. Notice the ContextMatcher scores 1.0 (perfect!)
3. It matches the podcast URL and timestamp is during playback
4. Preview shows it will be inserted with the timestamp
5. Apply and see it in history

### Example 3: Custom Input
1. Scroll down in the left pane
2. Type in the text area: **"TODO: Fix the login bug in production"**
3. Adjust the timestamp if you want
4. Click **"Match Custom Snippet"**
5. See which note it matches!

### Example 4: Ambiguous Match
1. Try a snippet that could match multiple notes
2. Watch the manual review modal appear
3. Compare the different options
4. Select the best match

## 🎨 What to Look For

### Matching Visualization (Middle Top)
- Each matcher shows its score as a colored bar
- Green bars = high confidence
- Hover to see exact percentages
- Read the reasoning below each match

### Preview (Middle Bottom)
- Shows the actual note content
- Yellow highlight = where new content will be inserted
- Full context so you can verify it makes sense

### History (Right)
- Every action logged with emoji + summary
- Recent actions at the top
- "MANUAL" badge for manual reviews
- Timestamps for each action

## 🔍 Advanced: Edit Timestamps for Time-Based Matching

The podcast/YouTube snippets have metadata with URLs and timestamps. To test the time-based gradual scoring:

1. Find snippet: **"[62:30] Final thoughts on distributed systems"**
   - This is AFTER the podcast ended (58 minutes)
   - Watch ContextMatcher give it a lower score (timestamp out of range)

2. Compare with: **"[15:23] Interesting point about CAP theorem"**
   - This is DURING the podcast
   - ContextMatcher scores it 1.0 (perfect!)

The algorithm:
- **5 min before podcast starts:** score 0.3 → 1.0 (gradual)
- **During podcast (0-58 min):** score 1.0 (perfect)
- **20 min after podcast ends:** score 1.0 → 0.5 (gradual)
- **Beyond window:** score 0.0

## 🐛 Troubleshooting

**"Failed to load data" error:**
- Backend not running → Check Terminal 1
- Wrong port → Backend should be on port 8000
- CORS issue → Check browser console for details

**Nothing happens when clicking snippets:**
- Open browser DevTools (F12)
- Check Console tab for errors
- Verify API calls are reaching `http://localhost:8000`

**Matchers show all zeros:**
- Check that test data loaded
- Visit: `http://localhost:8000/health`
- Should show `notes_count: 15, snippets_count: 15`

## 📊 Understanding the Scores

**High Score (80-100%):**
- Strong keyword overlap
- Structure pattern match
- Entity alignment
- Perfect time/URL context
- Project name match

**Medium Score (50-79%):**
- Partial keyword match
- Some entity overlap
- Close timestamp (in time window)
- Generic topic match

**Low Score (<50%):**
- Weak keyword overlap
- No clear pattern match
- Timestamp outside window
- Probably needs manual review

## 🎯 Test All 5 Matchers

1. **KeywordMatcher:** Try "shoe size" → scores high on Family Info
2. **StructureMatcher:** Try "- Name: Value" patterns
3. **EntityMatcher:** Try "XYZ project" → finds Project XYZ
4. **ContextMatcher:** Try podcast snippets with timestamps
5. **ProjectMatcher:** Try any snippet mentioning "project ABC"

## 💡 Tips

- Try custom inputs to see how the system handles new content
- Mix and match different types of information
- Watch how scores change with different keywords
- Notice when manual review triggers
- Check the history to see patterns in your sorting

## 🎓 Next Steps

After playing with the demo:
1. Review the code in `backend/matchers/` to see how each matcher works
2. Check `backend/scoring/aggregator.py` for score combination logic
3. Look at `backend/test_data/notes.json` to see the mock notes structure
4. Read the full README.md for architectural details

---

**Enjoy the demo!** 🎉 If something doesn't work, check the terminal outputs for error messages.
