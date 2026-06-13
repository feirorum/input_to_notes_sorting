# Design notes, critique, and what was added beyond the spec

This prototype implements the "Capture Inbox → Obsidian Sorter" spec, and then
deliberately fills the gaps that the spec left open — the ones that most affect
whether the system is *trustworthy* and whether the *next iteration* has the
hooks it needs. This file explains the architecture, the judgement calls, and
where I disagreed with or extended the brief.

## Core principle held throughout

**Never lose raw input.** Every capture is written verbatim to
`vault/inbox/<date>/item-NNN.md` *before* anything else happens
(`storage/inbox.py`). Classification, routing, and rewriting all read from that
saved copy. Nothing in the pipeline can destroy the original.

## Architecture (the modular seams the spec asked for)

```
capture adapters  ──►  inbox storage  ──►  classifier  ──►  policy  ──►  router
 (web form,            (raw .md +          (matchers,      (ask-rules)   (markdown
  POST, folder)         SQLite state)       scores)                       writer)
                                                                            │
                                          audit logger  ◄────────────────  ┘
                                          correction learner  ◄── review UI
```

- `app/capture/` — capture adapters (form/POST in `main.py`, folder import here).
- `app/storage/inbox.py` — raw, append-only inbox.
- `app/storage/vault.py` — Obsidian-compatible Markdown writer with **reversible**
  edits (snapshot-based undo).
- `app/storage/db.py` — SQLite as the source of truth for *state* (status, audit,
  learned examples, entity registry). Markdown is the source of truth for
  *content*.
- `app/classifier/` — pluggable, **explainable** classifier (`base.py` policy,
  `rules.py` matchers, `examples.py` similarity, `llm.py` Anthropic backend).
- `app/router.py` — the service that orchestrates the flow and owns state
  transitions, undo, and correction-learning.
- `app/audit.py` — structured (SQLite) + human-readable (Markdown) audit trail.
- `app/web/` — the demo/review UI.

The classifier is a clean interface (`classify(capture_id, text, ctx) -> Decision`)
with two backends behind it, exactly as the spec wanted ("rule-based first, then
LLM behind a clean interface").

## What the spec got right and we kept

- Ask only when confidence is low or the action is destructive/ambiguous;
  otherwise auto-sort and log everything. This is implemented as an explicit,
  single-source-of-truth **policy** (`base.apply_policy`) with the spec's ask /
  don't-ask rules encoded literally.
- Broad note *destinations*, not just tags.
- Structured decision objects, audit entries, undo, and corrections-as-examples.

## Critique of the spec, and the changes that follow from it

1. **The spec under-specifies "confidence". A single number isn't reviewable.**
   → Added an **explainable, multi-matcher scorer**. Every destination score is
   the sum of annotated `MatcherScore` contributions (keyword / entity / example
   / podcast), each carrying its own number *and a human explanation*. This is
   also what the README's evaluation pane needs — the middle pane shows exactly
   which matchers fired and with what score. Confidence is derived from the
   scores with an explicit ambiguity penalty, not pulled from a model's vibe.

2. **"Match a known person/project/podcast" is the strongest real-world signal,
   but the spec only mentions tags/keywords.**
   → Added an **entity registry** (`config.ENTITIES`, `entities` table). "Flora"
   reliably routes to `notes/family/flora.md` regardless of keyword soup, and
   the registry is what lets the agent detect when a capture would create a
   *new* long-lived entity (an explicit ask-trigger).

3. **"Corrections become examples" is stated but the feedback loop isn't closed
   — examples must actually change future behaviour.**
   → The **example-similarity matcher** scores new captures against saved
   corrections (token Jaccard), so a correction measurably moves future scores.
   `test_correction_learns_example_that_changes_future_scores` proves the loop.

4. **Undo is hand-waved ("store enough info to reverse").**
   → Undo is **snapshot-based and exact**: each mutation returns an
   `undo_payload` with the file's prior bytes (or a "created" marker so undo
   deletes the file). Reversal restores the prior content verbatim. A future
   iteration can swap this for git commits without changing the router contract.

5. **Tasks vs. knowledge is listed as an ask-trigger but needs detection.**
   → A task/reminder detector (`TASK_MARKERS`) flags action items and routes
   them to `leave_in_inbox_ask` rather than fabricating a knowledge note.

6. **Sensitivity handling needs teeth.**
   → A sensitivity detector forces a confirmation when private content has no
   clear destination (and is *not* suppressed by the "obvious destination" rule).

7. **Podcast session grouping is mentioned but vague.**
   → Timestamp extraction + a session hint that counts other recent timestamped
   captures, and proposed content that preserves `HH:MM — note` formatting.

8. **A demo that only shows the final answer can't be evaluated.**
   → `POST /explain` returns the full scored decision **plus a projected view of
   the target note** with the new line highlighted — without committing
   anything. This powers the three-pane evaluation UI the README asks for
   (example data → matchers & scores → where it lands).

9. **Separation of scoring from policy.** Safety-critical routing rules
   shouldn't live inside a model prompt or a keyword table. Policy is isolated in
   `base.apply_policy`, so the rule and LLM backends route identically once
   they've produced scores. The LLM only *scores*; deterministic code still
   extracts entities/timestamps and still applies the ask-rules.

## Notable judgement calls

- **SQLite for state, Markdown for content.** They're kept in sync by the
  router. This keeps the vault clean and Obsidian-friendly while giving us
  reliable status/undo/learning state.
- **Fail-safe LLM.** If `anthropic` isn't installed or the API call fails, the
  LLM/ensemble backend silently falls back to rules rather than erroring a
  capture. The default `CLASSIFIER=rules` runs with zero external dependencies
  or keys.
- **`leave_in_inbox_ask` vs `needs_review`.** Tasks and "we have a guess but want
  confirmation" stay actionable as `pending`; only genuinely unroutable items go
  to `needs_review`. The four spec actions are all used meaningfully.

## What I'd do next (future iterations)

- **Promote corrections to entities/aliases.** When a user repeatedly corrects
  captures about a new person to one note, auto-register an entity so keyword
  matching isn't needed thereafter.
- **Git-backed vault + per-change commits** for richer undo/history and conflict
  handling, replacing the snapshot undo.
- **Real podcast session linking** by title + time window + (optionally) URL
  title↔content matching, as the README hints.
- **Move routing rules into `vault/system/routing-rules.yaml`** so non-developers
  can edit destinations/keywords without touching code.
- **Capture adapters**: email/webhook and a Google Keep / share-target bridge.
- **Confidence calibration**: track correction rate per matcher and reweight
  contributions over time (the matcher breakdown is already logged for this).
- **Embeddings** for example similarity (the interface is already isolated in
  `examples.py`), once the simple token-overlap version proves insufficient.
- **Multi-item podcast merge**: actually combine grouped timestamped captures
  into one episode block rather than appending lines independently.
