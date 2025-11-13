# Sample Test Data for Input-to-Notes Sorting

## Test Dataset Structure

### Category: Work/Tasks
```
1. "TODO: Review the quarterly report before Friday's meeting"
2. "Need to schedule 1:1 with Sarah about the project timeline"
3. "Action item: Update documentation for the new API endpoints"
4. "Reminder: Submit expense report by end of month"
5. "Follow up with client about contract renewal"
```

### Category: Personal/Errands
```
1. "Buy milk, eggs, bread on the way home"
2. "Call dentist to schedule cleaning appointment"
3. "Pick up dry cleaning Thursday"
4. "Remember: Mom's birthday next week, order gift"
5. "Car needs oil change - make appointment"
```

### Category: Ideas/Projects
```
1. "Idea: Build a browser extension that auto-saves interesting quotes"
2. "Project idea: Personal dashboard showing all my metrics in one place"
3. "Could we use this approach for the mobile app redesign?"
4. "What if we combined the two features into a single workflow?"
5. "Interesting concept: Gamification for habit tracking"
```

### Category: Reading/Learning
```
1. "Article: The Architecture of Open Source Applications - https://example.com/article"
2. "Want to learn more about distributed consensus algorithms"
3. "Book recommendation: Designing Data-Intensive Applications"
4. "Tutorial on Rust async programming - save for later"
5. "Research paper: Attention Is All You Need (Transformers)"
```

### Category: Meeting/Events
```
1. "Team standup tomorrow 10am - discuss sprint planning"
2. "Coffee with Alex next Tuesday at 3pm downtown"
3. "Conference call with West Coast team - 2pm PST Thursday"
4. "Dentist appointment Wednesday 4:30pm"
5. "Webinar: Modern DevOps Practices - Friday 1pm (registered)"
```

### Category: Reference/Documentation
```
1. "Python string formatting guide: https://docs.python.org/3/library/string.html"
2. "Command to reset git branch: git reset --hard origin/main"
3. "Favorite VS Code keyboard shortcuts list"
4. "API key for production environment: stored in 1Password"
5. "How to configure nginx reverse proxy - step by step notes"
```

### Category: Journal/Reflection
```
1. "Today was productive - finally solved that performance issue"
2. "Feeling stuck on the architecture decision, need to think more"
3. "Great conversation with mentor about career direction"
4. "Realized I need better boundaries between work and personal time"
5. "Proud of how the presentation went, team seemed engaged"
```

### Category: Finance/Receipts
```
1. "Expense: $45.99 - AWS bill for December"
2. "Receipt: Coffee meeting with client - $28.50 (reimbursable)"
3. "Subscription renewed: GitHub Pro - $4/month"
4. "Invoice #12345 from contractor - $2,500 (due Jan 15)"
5. "Quarterly estimated tax payment reminder - $3,200"
```

---

## Edge Cases & Tricky Examples

### Multi-Category (Should pick primary or tag multiple)
```
1. "TODO: Read the article about machine learning optimization techniques before meeting"
   - Could be: Tasks, Reading, or Meetings
   - Primary: Tasks (action-oriented)
   - Tags: reading, meetings

2. "Expense: $35 for 'Clean Code' book (professional development)"
   - Could be: Finance or Reading
   - Primary: Finance (expense tracking)
   - Tags: reading, professional-development

3. "Idea: Maybe I should start a weekly reflection journal practice?"
   - Could be: Ideas or Journal
   - Primary: Ideas (consideration phase)
   - Secondary: If implemented → Journal
```

### Ambiguous/Low Confidence
```
1. "Interesting..."
   - Too vague, needs context

2. "Tomorrow"
   - Incomplete thought

3. "https://example.com/some-page"
   - URL without context
   - Action: Fetch page title/content?

4. "John"
   - Single name, no context

5. "!!!"
   - Pure emotion, unclear intent
```

### Complex Multi-Sentence
```
1. "Had a great insight during today's walk. What if instead of building
    a monolithic app, we split it into microservices? This could solve
    the scalability issues we've been having. TODO: Draft proposal for
    the team."
   - Contains: Reflection + Idea + Task
   - Primary: Tasks (ends with TODO)
   - Extract: One note with multiple tags

2. "Meeting notes from client call: They want 3 new features by Q2.
    Budget approved for $50k. Next steps: schedule kickoff meeting
    and create project plan."
   - Contains: Meeting notes + Finance + Tasks
   - Primary: Meetings
   - Action items extracted separately?
```

---

## Test Assertions

### High Confidence (>90% sure)
```yaml
Input: "TODO: Fix authentication bug"
Expected:
  category: "Work/Tasks"
  confidence: 0.95
  reasoning: "Clear TODO marker, technical context"

Input: "Buy groceries"
Expected:
  category: "Personal/Errands"
  confidence: 0.92
  reasoning: "Common household task"
```

### Medium Confidence (70-90%)
```yaml
Input: "Should I learn Go or Rust next?"
Expected:
  category: "Ideas/Projects" OR "Reading/Learning"
  confidence: 0.75
  reasoning: "Question about learning, but indecisive"
  action: "Suggest manual review or tag both"

Input: "Call with John about the proposal"
Expected:
  category: "Meetings" OR "Work/Tasks"
  confidence: 0.80
  reasoning: "Could be scheduled meeting or task to make call"
```

### Low Confidence (<70%)
```yaml
Input: "This is interesting"
Expected:
  category: "Unsorted/Inbox"
  confidence: 0.30
  reasoning: "No clear context or action"
  action: "Manual review required"
```

---

## Performance Test Dataset

### Small Scale (100 items)
- 10 per category across 10 categories
- Balanced distribution
- Known labels for accuracy calculation
- Purpose: Development testing

### Medium Scale (1000 items)
- Realistic distribution (not balanced)
  - Tasks: 200
  - Reading: 150
  - Ideas: 100
  - Meetings: 100
  - Journal: 150
  - Reference: 100
  - Personal: 100
  - Finance: 50
  - Other: 50
- Mix of easy and tricky examples
- Purpose: Integration testing

### Large Scale (10,000 items)
- Simulated real-world usage over 6 months
- Natural distribution patterns
- Include seasonal variations (tax season → more finance)
- Purpose: Performance and scalability testing

---

## Validation Metrics Template

```python
{
  "test_run_id": "2025-01-15-001",
  "total_items": 100,
  "correct": 87,
  "acceptable": 7,
  "wrong": 4,
  "failed": 2,
  "accuracy": 0.87,
  "precision_by_category": {
    "Work/Tasks": 0.92,
    "Personal/Errands": 0.95,
    "Ideas/Projects": 0.78,
    "Reading/Learning": 0.85,
    "Meetings": 0.90,
    "Reference": 0.82,
    "Journal": 0.88,
    "Finance": 0.94
  },
  "avg_processing_time_ms": 45,
  "p95_processing_time_ms": 120,
  "errors": [
    {
      "input": "TODO: Read the article before meeting",
      "predicted": "Reading",
      "actual": "Tasks",
      "reasoning": "Focused on 'read' instead of 'TODO'"
    }
  ]
}
```

---

## Continuous Learning Examples

### User Corrections Feed Training
```
Week 1: User corrects 15 items
  - "Webinar registration" from Reading → Meetings (3x)
  - "Newsletter links" from Reading → Reference (5x)
  - Pattern detected: Update rules

Week 4: Same patterns appear
  - Accuracy improved from 82% → 89%
  - Webinar now correctly classified
  - Newsletter routing refined
```

### Adaptive Categories
```
Month 1: User has 8 categories
Month 3: User creates "Health/Fitness" category
  - System needs to learn this new category
  - Provide examples or ask for 10 samples
  - Start routing health-related inputs

Month 6: "Health/Fitness" splits into:
  - "Health/Medical"
  - "Health/Fitness"
  - Re-train or update rules
```

---

## Integration Test Scenarios

### Scenario: Email Morning Triage
```python
# Input: 20 emails from overnight
emails = [
  {"from": "newsletter@...", "subject": "5 Tips for Better Sleep", "body": "..."},
  {"from": "boss@...", "subject": "URGENT: Client issue", "body": "..."},
  {"from": "amazon@...", "subject": "Your order has shipped", "body": "..."},
  # ... 17 more
]

# Expected output
sorted_emails = {
  "Reading/Newsletters": [email_1, email_7, email_12],
  "Work/Urgent": [email_2, email_5],
  "Work/FYI": [email_3, email_8, email_9, email_15],
  "Personal/Shopping": [email_3, email_18],
  "Finance/Receipts": [email_19],
  "Archive": [email_4, email_6, email_10, email_11, email_13, email_14,
              email_16, email_17, email_20]
}

# Success criteria: 18+ correctly sorted (90%)
```

### Scenario: Capture Tool Integration
```python
# From various sources throughout the day
inputs = [
  {"source": "voice_note", "content": "Remind me to call Sarah tomorrow",
   "timestamp": "09:30"},
  {"source": "web_clipper", "url": "...", "content": "Article about Rust",
   "timestamp": "10:15"},
  {"source": "quick_note", "content": "Project idea: automation dashboard",
   "timestamp": "14:20"},
  {"source": "screenshot", "ocr_text": "Error: Connection timeout",
   "timestamp": "16:45"},
]

# Should route to appropriate systems
# Voice → Calendar/Tasks
# Web clip → Reading list
# Quick note → Ideas backlog
# Screenshot → Technical notes/Troubleshooting
```
