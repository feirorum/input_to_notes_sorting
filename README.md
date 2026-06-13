# Capture Inbox → Obsidian Sorter

A local-first prototype that receives quick notes, **always saves them raw
first**, then uses an explainable agent to classify and route them into an
Obsidian-compatible Markdown vault — with a full audit log and undo/correct/learn
support.

> Original idea: a notes/knowledgebase/snippet system that ingests snippets
> (things heard on a podcast, watched on YouTube, quick thoughts) and sorts them
> into the right existing notes — e.g. "Sam's shoe size is now 34" → the family
> note with the other sizes; "input from security on XYZ" → the XYZ project note;
> timestamped podcast notes → the matching podcast note.

See **[DESIGN.md](DESIGN.md)** for the architecture, a critique of the original
spec, and the improvements added on top of it.

## Quick start (one command)

```bash
./run.sh
```

Then open <http://127.0.0.1:8000>. Runs with **no API key** using the
rule-based classifier. To use the LLM backend instead:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
CLASSIFIER=ensemble ./run.sh        # rules + LLM, or CLASSIFIER=llm
```

Run the tests:

```bash
. .venv/bin/activate && pytest -q
```

## The evaluation demo (three panes)

The home page is built for inspecting *how* a decision is made, matching this
repo's evaluation requirement:

1. **Capture** — trigger an example note or type one. "Explain (dry run)" scores
   it without changing anything.
2. **Matchers & scores** — the decision (action, confidence, why it's asking),
   signals (task / sensitive / entity / timestamps), and a table of every
   destination's score broken down by matcher, each with an explanation.
3. **Where it lands** — the target note's content *after* sorting, with the new
   line highlighted.

Below the panes, the workflow tabs (**Inbox / Needs review / Processed / Audit**)
let you Process inbox items, Confirm or Correct proposals, and Undo changes.

## How routing works

Each capture is scored by independent, explainable matchers:

- **entity** — names a known person/project/podcast → its note (strongest signal)
- **keyword** — destination keyword hits
- **example** — similarity to a saved correction (this is how feedback changes
  future routing)
- **podcast** — timestamps / "podcast"/"episode" → podcast note, with session
  grouping

A single **policy** then decides whether to act automatically, ask for
confirmation, or send to review. It **asks** when confidence is low, destinations
tie, the note is a task/reminder, it's sensitive with no clear home, or it would
create a new long-lived note. It **doesn't ask** when a known entity or a saved
correction makes the destination obvious and the change is reversible.

## API

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/capture` | Save a raw note to the inbox |
| GET  | `/inbox` | List unprocessed captures |
| POST | `/import` | Import a folder of `.md`/`.txt` files |
| POST | `/process/{id}` | Classify + route (auto or ask) |
| POST | `/confirm/{id}` | Apply a pending proposed decision |
| POST | `/correct/{id}` | Re-route + save the correction as an example |
| POST | `/undo/{id}` | Reverse the last change for a capture |
| GET  | `/review` | Pending + needs-review items with proposals |
| GET  | `/processed` | Processed items |
| GET  | `/audit` | Audit log |
| POST | `/explain` | Score a note without committing (drives the demo) |
| GET  | `/config` | Destinations, entities, thresholds |

## Vault layout

```
vault/
  inbox/<date>/item-NNN.md           # raw captures (gitignored, generated)
  notes/<category>/*.md              # the sorted Obsidian notes
  system/routing-rules.md            # human-readable routing rules
  system/classification-examples.md  # saved corrections
  audit-log/<date>.md                # human-readable audit trail
```

State (status, audit, learned examples, entity registry) lives in `sorter.db`
(SQLite); the Markdown files are the human-facing content. See DESIGN.md for why.

## Non-goals (v1)

Perfect mobile/Keep/reMarkable integration, a vector DB, multi-user, and a
polished UI. The architecture is modular so these can be added without rewrites.
