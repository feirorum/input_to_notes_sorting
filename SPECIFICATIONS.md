# Technical Specifications for Note Sorting System

## Architecture Overview

```
┌─────────────┐
│   Snippet   │
│    Input    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│     Content Type Detector               │
│  (URL/Code/Text/Timestamp)              │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│     Matcher Orchestrator                │
│  (runs enabled matchers in parallel)    │
└──────┬──────────────────────────────────┘
       │
       ├─────► Keyword Matcher
       ├─────► Semantic Matcher
       ├─────► Rule-Based Matcher
       ├─────► NER Matcher
       ├─────► Content-Type Specific Matcher
       │
       ▼
┌─────────────────────────────────────────┐
│     Hybrid Scorer                       │
│  (combines weighted scores)             │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Confidence Threshold Check             │
│  (auto-sort vs disambiguation)          │
└──────┬──────────────────────────────────┘
       │
       ├─────► Auto-sort (high confidence)
       └─────► Interactive Disambiguation (low confidence)
```

---

## 1. Simple Keyword Matcher

### Specification

**Input:**
- Snippet text (string)
- List of existing notes (with title, content, metadata)

**Output:**
- Array of matches: `[{noteId, score, matchedKeywords}]`

**Algorithm:**
1. Preprocess snippet:
   - Lowercase
   - Remove stopwords
   - Extract keywords (words with length > 2)
   - Extract n-grams (2-3 words)
2. For each note:
   - Calculate TF-IDF scores for keywords
   - Bonus for title matches (3x weight)
   - Bonus for exact phrase matches (2x weight)
   - Bonus for keyword frequency
3. Return sorted matches with score > threshold (0.1)

**Configuration:**
```javascript
{
  enabled: true,
  minScore: 0.1,
  titleWeight: 3.0,
  phraseMatchBonus: 2.0,
  stopwords: ['the', 'a', 'an', 'in', 'on', ...],
  minKeywordLength: 3
}
```

**API:**
```javascript
class KeywordMatcher {
  constructor(config);
  match(snippet, notes): Promise<Match[]>;
  extractKeywords(text): string[];
  calculateTFIDF(keywords, document): number;
}
```

**Testing:**
- "Sam's shoe size is now 34" → should match note with title "Family Shoe Sizes"
- "XYZ project update" → should match note containing "XYZ project"

---

## 2. Semantic Similarity Matcher

### Specification

**Input:**
- Snippet text
- Pre-computed embeddings for all notes (or compute on demand)

**Output:**
- Array of matches: `[{noteId, score, similarity}]`

**Algorithm:**
1. Generate embedding for snippet using Sentence-BERT
2. Load or compute embeddings for all notes
3. Calculate cosine similarity between snippet and each note
4. Return matches with similarity > threshold (0.5)

**Dependencies:**
- `@xenova/transformers` (browser-compatible transformers)
- Model: `Xenova/all-MiniLM-L6-v2` (lightweight, good quality)

**Configuration:**
```javascript
{
  enabled: true,
  model: 'Xenova/all-MiniLM-L6-v2',
  minSimilarity: 0.5,
  useCache: true,
  batchSize: 32
}
```

**Caching Strategy:**
- Store embeddings in IndexedDB
- Recompute only when note content changes
- LRU cache for recent computations

**API:**
```javascript
class SemanticMatcher {
  constructor(config);
  match(snippet, notes): Promise<Match[]>;
  computeEmbedding(text): Promise<Float32Array>;
  cosineSimilarity(vec1, vec2): number;
  getOrComputeNoteEmbedding(note): Promise<Float32Array>;
}
```

**Testing:**
- "vehicle maintenance" should match "car repairs" note
- "footwear measurements" should match "shoe sizes" note

---

## 3. Rule-Based Category System

### Specification

**Input:**
- Snippet text
- User-defined rules (JSON)

**Output:**
- Array of matches: `[{noteId, score: 1.0, matchedRules}]` (binary match)

**Rule Format:**
```javascript
{
  id: 'rule-1',
  noteId: 'note-xyz',
  priority: 1,
  conditions: {
    type: 'AND', // or 'OR', 'NOT'
    rules: [
      {type: 'keyword', value: 'project', caseSensitive: false},
      {type: 'regex', value: 'XYZ|ABC'},
      {type: 'contains', value: 'security'}
    ]
  }
}
```

**Algorithm:**
1. Load rules sorted by priority (ascending)
2. For each rule, evaluate conditions:
   - keyword: simple string contains
   - regex: test against pattern
   - contains: substring match
   - startsWith/endsWith: position-specific
3. Apply boolean logic (AND/OR/NOT)
4. Return first match (highest priority) or all matches

**Configuration:**
```javascript
{
  enabled: true,
  rules: [...],
  matchMode: 'first' | 'all', // stop at first match or return all
  allowOverride: true // can other matchers override rule matches
}
```

**API:**
```javascript
class RuleBasedMatcher {
  constructor(config);
  match(snippet, notes): Promise<Match[]>;
  evaluateRule(rule, snippet): boolean;
  validateRule(rule): boolean; // for rule builder
  testRule(rule, testSnippet): boolean; // for testing
}
```

**Visual Rule Builder:**
- Drag-and-drop condition blocks
- Live preview with test snippets
- Export/import rules as JSON

---

## 4. Interactive Disambiguation

### Specification

**Input:**
- Snippet
- All matcher results with scores
- Confidence threshold

**Output:**
- If max_score > threshold: auto-select top match
- If max_score <= threshold: return top N for user selection

**Algorithm:**
1. Collect all match results from matchers
2. Calculate confidence = max(scores) / sum(scores)
3. If confidence > threshold (0.7):
   - Auto-sort to top match
   - Show notification
4. Else:
   - Show disambiguation UI
   - Present top 3-5 candidates
   - Include "create new note" option

**Configuration:**
```javascript
{
  enabled: true,
  confidenceThreshold: 0.7,
  maxSuggestions: 5,
  autoSortIfSingleMatch: true,
  rememberChoices: true // learn from user selections
}
```

**UI Components:**
```javascript
// Disambiguation modal
<DisambiguationModal>
  <Snippet text={snippet} />
  <Suggestions>
    {suggestions.map(s => (
      <SuggestionCard
        note={s.note}
        score={s.score}
        reasoning={s.reasoning}
        onSelect={() => selectNote(s)}
      />
    ))}
  </Suggestions>
  <Actions>
    <Button>Create New Note</Button>
    <Button>Skip</Button>
  </Actions>
</DisambiguationModal>
```

**Keyboard Shortcuts:**
- `1-5`: Select suggestion 1-5
- `n`: Create new note
- `s`: Skip
- `Escape`: Cancel

**API:**
```javascript
class InteractiveDisambiguation {
  constructor(config);
  shouldDisambiguate(matches): boolean;
  presentChoices(snippet, matches): Promise<Selection>;
  recordChoice(snippet, selectedNote): void; // for learning
}
```

---

## 5. Content-Type Specific Matchers

### Specification

**Content Type Detection:**
```javascript
const detectContentType = (snippet) => {
  if (isURL(snippet)) return 'url';
  if (isCode(snippet)) return 'code';
  if (hasTimestamp(snippet)) return 'timestamp';
  return 'text';
};
```

### 5.1 URL Matcher

**Input:** URL string
**Processing:**
1. Extract domain
2. Fetch metadata (title, description) if possible
3. Match against notes containing same domain
4. Match against notes with similar titles

**Configuration:**
```javascript
{
  enabled: true,
  fetchMetadata: true,
  matchDomain: true,
  domainWeight: 2.0,
  titleWeight: 3.0
}
```

### 5.2 Code Snippet Matcher

**Input:** Code text
**Processing:**
1. Detect language (heuristics or library)
2. Extract imports/includes
3. Extract function/class names
4. Match against notes with same language
5. Match against notes containing similar imports

**Configuration:**
```javascript
{
  enabled: true,
  languageDetection: true,
  extractImports: true,
  extractNames: true,
  languageWeight: 1.5
}
```

### 5.3 Timestamp Matcher

**Input:** Text with timestamp reference
**Processing:**
1. Extract timestamp/date references
2. Match against notes created near that time
3. Match against calendar events
4. Match against notes mentioning same date

**Configuration:**
```javascript
{
  enabled: true,
  timeWindow: '7d', // match within 7 days
  dateFormats: ['ISO', 'US', 'EU'],
  matchCalendar: true
}
```

**API:**
```javascript
class ContentTypeSpecificMatcher {
  constructor(config);
  detectType(snippet): ContentType;
  matchURL(url, notes): Promise<Match[]>;
  matchCode(code, notes): Promise<Match[]>;
  matchTimestamp(text, notes): Promise<Match[]>;
  matchText(text, notes): Promise<Match[]>; // fallback to keyword
}
```

---

## 6. Named Entity Recognition (NER) Matcher

### Specification

**Input:**
- Snippet text

**Output:**
- Extracted entities with types
- Matches based on entity overlap

**Algorithm:**
1. Run NER on snippet (using simple regex-based NER initially)
2. Extract entities:
   - PERSON: Names (capitalized words)
   - ORG: Organizations
   - PROJECT: Project names (format: uppercase acronyms or "X project")
   - DATE: Date references
   - LOCATION: Place names
3. Build entity index for all notes (cached)
4. Match based on entity overlap:
   - score = (shared_entities) / (total_entities)
5. Weight by entity type (PROJECT > PERSON > ORG > DATE > LOCATION)

**Entity Detection (Simple Version):**
```javascript
const detectEntities = (text) => {
  const entities = [];

  // PROJECT: uppercase acronyms or "X project"
  const projects = text.match(/\b[A-Z]{2,}\b|(\w+)\s+project/gi);

  // PERSON: capitalized words (after filtering common words)
  const persons = text.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b/g);

  // DATE: common date patterns
  const dates = text.match(/\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}\/\d{4}/g);

  return { projects, persons, dates };
};
```

**Configuration:**
```javascript
{
  enabled: true,
  entityWeights: {
    PROJECT: 3.0,
    PERSON: 2.0,
    ORG: 2.0,
    DATE: 1.0,
    LOCATION: 1.0
  },
  minEntityOverlap: 0.3,
  buildIndex: true
}
```

**API:**
```javascript
class NERMatcher {
  constructor(config);
  match(snippet, notes): Promise<Match[]>;
  extractEntities(text): Entity[];
  buildEntityIndex(notes): EntityIndex;
  matchByEntities(entities, index): Match[];
}
```

**Visualization:**
- Highlight entities in snippet with color-coding by type
- Show entity cards on hover
- Display "notes mentioning [Entity]" list

---

## 7. Hybrid Weighted Scoring System

### Specification

**Purpose:** Combine results from all matchers with configurable weights.

**Input:**
- Array of match results from all enabled matchers
- Weight configuration

**Output:**
- Unified match list with combined scores

**Algorithm:**
1. Collect matches from all matchers: `{matcher: string, noteId: string, score: number}[]`
2. Group by noteId
3. For each note:
   ```
   finalScore = Σ(matcherScore_i × weight_i) / Σ(weight_i)
   ```
4. Normalize scores to [0, 1]
5. Sort by finalScore descending

**Configuration:**
```javascript
{
  enabled: true,
  weights: {
    keyword: 1.0,
    semantic: 2.0,
    rules: 3.0,      // highest - user-defined rules should win
    ner: 1.5,
    contentType: 1.5
  },
  normalizationMethod: 'minmax' | 'zscore' | 'softmax',
  combineMethod: 'weighted-sum' | 'multiply' | 'max'
}
```

**Score Breakdown Visualization:**
```javascript
{
  noteId: 'note-123',
  finalScore: 0.85,
  breakdown: {
    keyword: { score: 0.6, weight: 1.0, contribution: 0.15 },
    semantic: { score: 0.9, weight: 2.0, contribution: 0.45 },
    rules: { score: 1.0, weight: 3.0, contribution: 0.75 },
    ner: { score: 0.7, weight: 1.5, contribution: 0.26 }
  }
}
```

**API:**
```javascript
class HybridScorer {
  constructor(config);
  combineMatches(matcherResults): Promise<Match[]>;
  normalizeScores(scores): number[];
  calculateBreakdown(noteId, matcherResults): Breakdown;
  optimizeWeights(historicalData): WeightConfig; // future: ML-based
}
```

**Weight Tuning UI:**
- Sliders for each matcher weight
- Live preview with example snippets
- A/B test framework
- Historical accuracy metrics

---

## Data Models

### Snippet
```typescript
interface Snippet {
  id: string;
  text: string;
  source?: string; // 'podcast', 'youtube', 'manual', etc
  timestamp: Date;
  metadata?: {
    url?: string;
    title?: string;
    author?: string;
    [key: string]: any;
  };
}
```

### Note
```typescript
interface Note {
  id: string;
  title: string;
  content: string;
  createdAt: Date;
  updatedAt: Date;
  tags?: string[];
  category?: string;
  metadata?: {
    embedding?: Float32Array;
    entities?: Entity[];
    [key: string]: any;
  };
}
```

### Match
```typescript
interface Match {
  noteId: string;
  score: number; // [0, 1]
  matcher: string; // which matcher produced this
  reasoning?: string; // human-readable explanation
  matchedTerms?: string[]; // keywords, entities, etc that matched
  confidence?: number; // optional: different from score
}
```

### Entity
```typescript
interface Entity {
  text: string;
  type: 'PERSON' | 'ORG' | 'PROJECT' | 'DATE' | 'LOCATION' | 'OTHER';
  startPos: number;
  endPos: number;
  confidence?: number;
}
```

---

## Feature Flags

### Global Config
```javascript
const CONFIG = {
  matchers: {
    keyword: { enabled: true, ...keywordConfig },
    semantic: { enabled: true, ...semanticConfig },
    rules: { enabled: true, ...rulesConfig },
    ner: { enabled: true, ...nerConfig },
    contentType: { enabled: true, ...contentTypeConfig },
    interactive: { enabled: true, ...interactiveConfig },
    hybrid: { enabled: true, ...hybridConfig }
  },
  demo: {
    showScoreBreakdown: true,
    showMatcherViz: true,
    enableDebugMode: true
  }
};
```

### Environment Variables
```bash
ENABLE_KEYWORD_MATCHER=true
ENABLE_SEMANTIC_MATCHER=true
ENABLE_RULES_MATCHER=true
ENABLE_NER_MATCHER=true
ENABLE_CONTENT_TYPE_MATCHER=true
ENABLE_INTERACTIVE_DISAMBIGUATION=true
ENABLE_HYBRID_SCORER=true
```

---

## Demo Web Interface

### Layout (3-panel design as per requirements)

```
┌─────────────────────────────────────────────────────────────┐
│                         Header                               │
│  [Logo] Note Sorting System Demo    [Settings] [GitHub]     │
├──────────────┬──────────────────────┬────────────────────────┤
│              │                      │                        │
│  Left Panel  │    Middle Panel      │     Right Panel        │
│   (Input)    │    (Matching)        │     (Results)          │
│              │                      │                        │
│ ┌──────────┐ │ ┌──────────────────┐ │ ┌────────────────────┐ │
│ │ Example  │ │ │ Active Matchers  │ │ │ Target Note        │ │
│ │ Snippets │ │ │                  │ │ │                    │ │
│ │          │ │ │ ☑ Keyword  78%  │ │ │ Family Shoe Sizes  │ │
│ │ • Shoe   │ │ │ ☑ Semantic 85%  │ │ │                    │ │
│ │   size   │ │ │ ☑ Rules    100% │ │ │ Content:           │ │
│ │ • Project│ │ │ ☑ NER      65%  │ │ │ - Sam: 32 (2023)   │ │
│ │   update │ │ │ ☐ Content  —    │ │ │ - Emma: 28 (2023)  │ │
│ │ • Podcast│ │ │                  │ │ │ + Sam: 34 (new)    │ │
│ │          │ │ │ Combined: 89%   │ │ │                    │ │
│ │ [Custom] │ │ │                  │ │ │ Matched by:        │ │
│ │          │ │ │ Score Breakdown: │ │ │ • "shoe size" (kw) │ │
│ │ ┌──────┐ │ │ │ [===Chart===]   │ │ │ • "Sam" (NER)      │ │
│ │ │      │ │ │ │                  │ │ │ • Rule #3          │ │
│ │ │      │ │ │ └──────────────────┘ │ └────────────────────┘ │
│ │ └──────┘ │ │                      │                        │
│ │          │ │ Other Candidates:    │ All Notes:             │
│ │ [Try It] │ │ • Project Notes 45% │ • Family Shoe Sizes    │
│ └──────────┘ │ • Random Note  12%  │ • XYZ Project          │
│              │                      │ • Podcast Notes        │
└──────────────┴──────────────────────┴────────────────────────┘
```

### Features:
1. **Left Panel:**
   - Pre-made example snippets
   - Custom input textarea
   - Content type indicator
   - Source metadata inputs

2. **Middle Panel:**
   - Real-time matcher execution
   - Score visualization (progress bars)
   - Score breakdown chart
   - Matcher contribution pie chart
   - Confidence indicator
   - Reasoning/explanation text

3. **Right Panel:**
   - Top matched note (highlighted)
   - Preview of where snippet will be inserted
   - Before/after diff view
   - List of other candidate matches
   - All available notes (collapsible)

4. **Interactive Elements:**
   - Hover over matchers to see details
   - Click matcher to toggle enable/disable
   - Adjust weights with sliders (in settings)
   - Click on note to see full content
   - Drag snippet to manually assign

---

## Testing Strategy

### Unit Tests
- Each matcher independently
- Edge cases (empty input, no matches, ties)
- Configuration validation

### Integration Tests
- Matcher orchestration
- Hybrid scoring
- Feature flag toggling

### End-to-End Tests
- Full flow: input → matching → display
- Example scenarios from README
- Performance benchmarks

### Test Data
```javascript
const TEST_SNIPPETS = [
  {
    text: "Sam's shoe size is now 34",
    expectedNote: "Family Shoe Sizes",
    expectedMatchers: ["keyword", "ner"]
  },
  {
    text: "We got the input needed from security, on the xyz project",
    expectedNote: "XYZ Project",
    expectedMatchers: ["keyword", "ner", "rules"]
  }
];
```

---

## Performance Targets

- Keyword matching: < 50ms
- Semantic matching: < 200ms (with cached embeddings)
- Rule evaluation: < 10ms
- NER extraction: < 100ms
- Total (all matchers): < 500ms
- Demo UI: 60fps animations, < 100ms interaction response
