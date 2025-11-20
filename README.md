# Note Sorting System - Experimentation Repository

An intelligent system for automatically sorting and categorizing input snippets (from podcasts, YouTube, manual input, etc.) into relevant notes using multiple matching strategies.

## Overview

This repo implements **7 different matching approaches** that can be used individually or combined to intelligently sort snippets into the right notes:

1. **Keyword Matching** - TF-IDF based keyword extraction and matching
2. **Rule-Based System** - User-defined rules with boolean logic
3. **Named Entity Recognition (NER)** - Entity extraction and matching
4. **Content-Type Specific Matchers** - Different strategies for URLs, code, timestamps
5. **Hybrid Weighted Scoring** - Combines multiple matchers with configurable weights
6. **Interactive Disambiguation** - Asks user when confidence is low
7. **Semantic Similarity** - *(Framework ready, requires external dependencies)*

All approaches are implemented **side-by-side** with **feature flags** allowing you to enable/disable and test each independently.

## Demo

The system includes a **3-panel web demo** as specified:

- **Left Panel:** Input snippets (examples + custom input)
- **Middle Panel:** Matching process visualization (active matchers, scores, breakdown)
- **Right Panel:** Results (best match, insertion preview, all notes)

### Running the Demo

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

Then open http://localhost:3000 in your browser.

## Project Structure

```
.
├── src/
│   ├── core/
│   │   ├── types.js              # TypeScript-style type definitions
│   │   ├── config.js             # Configuration system with defaults
│   │   └── MatcherOrchestrator.js # Coordinates all matchers
│   ├── matchers/
│   │   ├── KeywordMatcher.js     # TF-IDF keyword matching
│   │   ├── RuleBasedMatcher.js   # User-defined rules engine
│   │   ├── NERMatcher.js         # Named entity recognition
│   │   ├── ContentTypeMatcher.js # Content-type specific matching
│   │   ├── HybridScorer.js       # Weighted score combiner
│   │   └── index.js              # Matcher exports
│   ├── utils/
│   │   └── text.js               # Text processing utilities
│   └── data/
│       └── testData.js           # Example notes, snippets, and rules
├── demo/
│   ├── app.js                    # Demo application logic
│   ├── styles/
│   │   └── main.css              # Demo styling
│   └── components/               # (Future: React components)
├── index.html                    # Demo entry point
├── vite.config.js                # Vite configuration
├── package.json
├── SORTING_IDEAS.md              # 15 brainstormed approaches
├── SELECTED_APPROACHES.md        # 7 chosen approaches with rationale
└── SPECIFICATIONS.md             # Detailed technical specs
```

## Feature Flags

All matchers can be toggled via configuration:

```javascript
const config = {
  matchers: {
    keyword: { enabled: true },
    rules: { enabled: true },
    ner: { enabled: true },
    contentType: { enabled: true },
    semantic: { enabled: false },
    interactive: { enabled: true },
    hybrid: { enabled: true }
  }
};
```

Toggle in the UI via the **Settings** button or programmatically via `orchestrator.toggleMatcher(name, enabled)`.

## Example Usage

### Programmatic API

```javascript
import { MatcherOrchestrator } from './src/core/MatcherOrchestrator.js';
import { getConfig } from './src/core/config.js';

const orchestrator = new MatcherOrchestrator(getConfig());

const snippet = {
  id: '1',
  text: "Sam's shoe size is now 34",
  source: 'manual',
  timestamp: new Date()
};

const notes = [
  {
    id: 'note-1',
    title: 'Family Shoe Sizes',
    content: 'Sam: 32 (2023), Emma: 28 (2023)',
    createdAt: new Date(),
    updatedAt: new Date()
  }
];

const result = await orchestrator.matchSnippet(snippet, notes);

console.log(result.matches);
// [{ noteId: 'note-1', score: 0.85, matcher: 'hybrid', ... }]

console.log(result.needsDisambiguation);
// false (high confidence)

console.log(result.topMatches);
// Top 5 candidate matches
```

### UI Demo

The demo provides:

1. **Pre-made example snippets** matching the original requirements:
   - "Sam's shoe size is now 34" → Family Shoe Sizes note
   - "We got input from security on XYZ project" → XYZ Project note
   - Podcast notes with timestamps
   - Code snippets
   - URLs

2. **Custom input** - Enter any text and see how it matches

3. **Live matching visualization**:
   - Each matcher's score displayed as progress bar
   - Color-coded by matcher type
   - Score breakdown chart for hybrid results

4. **Interactive settings**:
   - Toggle matchers on/off
   - Adjust hybrid scorer weights
   - Configure confidence threshold

## Matchers Overview

### 1. Keyword Matcher

Uses TF-IDF scoring with:
- Stopword removal
- N-gram extraction (bigrams, trigrams)
- Title match bonus (3x weight)
- Phrase match bonus (2x weight)

**Best for:** Exact term matching, project names, specific keywords

### 2. Rule-Based Matcher

User-defined rules with:
- Boolean logic (AND/OR/NOT)
- Multiple condition types (keyword, regex, contains, startsWith, etc.)
- Priority ordering
- Visual rule builder (planned)

**Best for:** Well-defined categories, strict matching requirements

### 3. NER Matcher

Extracts and matches:
- PROJECT entities (acronyms, "X project")
- PERSON names
- ORGANIZATION names
- DATES
- LOCATIONS

**Best for:** Notes about people, projects, organizations

### 4. Content-Type Matcher

Specialized matching for:
- **URLs:** Domain and title matching
- **Code:** Language detection, import/function extraction
- **Timestamps:** Date/time pattern matching
- **Text:** Fallback to keyword matching

**Best for:** Mixed content types, URLs, code snippets

### 5. Hybrid Scorer

Combines multiple matchers with configurable weights:
- Weighted sum (default)
- Geometric mean (multiply)
- Max score

Provides score breakdown for transparency.

**Best for:** Production use, highest accuracy

### 6. Interactive Disambiguation

When confidence < threshold:
- Shows top N candidates
- User selects correct match
- Records choice for learning

**Best for:** Handling edge cases, building training data

## Configuration

Configuration is stored in `localStorage` and can be modified via:

```javascript
import { getConfig, saveConfig, resetConfig } from './src/core/config.js';

const config = getConfig();
config.matchers.keyword.minScore = 0.2;
saveConfig(config);

// Or reset to defaults
resetConfig();
```

### Default Weights

```javascript
{
  keyword: 1.0,
  semantic: 2.0,
  rules: 3.0,      // Highest - user intent should win
  ner: 1.5,
  contentType: 1.5
}
```

## Example Test Cases

From `testData.js`:

| Snippet | Expected Match | Matchers Used |
|---------|---------------|---------------|
| "Sam's shoe size is now 34" | Family Shoe Sizes | keyword, NER (Sam) |
| "Got input from security on XYZ project" | XYZ Project Notes | keyword, NER (XYZ), rules |
| "Podcast @15:30 about prompt engineering" | Podcast: AI Revolution | keyword, timestamp, rules |
| `function calculateTotal(items) {...}` | JavaScript Best Practices | content-type (code) |
| URL to GitHub repo | Book Notes: Clean Code | content-type (URL) |

## Development

### Adding a New Matcher

1. Create `src/matchers/YourMatcher.js`:

```javascript
export class YourMatcher {
  constructor(config) {
    this.config = config;
    this.enabled = config.enabled !== false;
  }

  async match(snippet, notes) {
    // Return array of { noteId, score, matcher, reasoning, matchedTerms }
    return [];
  }
}
```

2. Add to `MatcherOrchestrator.js`
3. Add config to `config.js`
4. Update UI in `demo/app.js`

### Testing

```bash
npm test
```

(Tests to be added - see SPECIFICATIONS.md for test strategy)

## Documentation

- **SORTING_IDEAS.md** - 15 brainstormed approaches with pros/cons
- **SELECTED_APPROACHES.md** - 7 chosen approaches and rationale
- **SPECIFICATIONS.md** - Detailed technical specs for each matcher

## Future Enhancements

- [ ] Semantic similarity matcher (requires ML dependencies)
- [ ] Machine learning classifier (active learning)
- [ ] Graph-based knowledge relationships
- [ ] Learning from user corrections
- [ ] React component library
- [ ] Browser extension
- [ ] Mobile app
- [ ] API server

## Use Cases

This system is designed for:

- **Personal knowledge management** - Organize notes from multiple sources
- **Research notes** - Automatically categorize research snippets
- **Meeting notes** - Sort action items into project notes
- **Learning notes** - Organize podcast/video notes by topic
- **Code snippets** - Categorize code examples by language/framework

## License

MIT

## Contributing

This is an experimental repository. Feel free to:
- Try different matching strategies
- Experiment with weights and thresholds
- Add new matchers
- Improve UX

See [SPECIFICATIONS.md](SPECIFICATIONS.md) for architecture details.
