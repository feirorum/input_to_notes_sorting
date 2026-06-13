"""Classifier interface, shared context, and the decision policy.

The *policy* (when to act vs. ask vs. review) lives here, separate from the
*scoring* (rules.py / llm.py). This is the single place the ask-rules from the
spec are encoded, so both backends route the same way once they've produced
scores. Keeping policy out of scoring is what lets the demo show "the scores
said X, the policy decided Y, here's why".
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Optional, Protocol

from .. import config
from ..models import (Action, Decision, DestinationScore, MatcherScore)

TIMESTAMP_RE = re.compile(r"\b(\d{1,2}:\d{2})\b")


@dataclass
class ClassifierContext:
    """Everything a matcher needs that comes from outside the text itself."""
    entities: list[dict]            # name, destination_key, note_path, aliases, kind
    examples: list[dict]            # learned corrections
    note_exists: "callable"         # (rel_path) -> bool
    recent_texts: list[str]         # recent capture texts (podcast grouping)


class Classifier(Protocol):
    def classify(self, capture_id: str, text: str,
                 ctx: ClassifierContext) -> Decision:
        ...


# --- shared scoring helpers ------------------------------------------------

def detect_task(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in config.TASK_MARKERS)


def detect_sensitive(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in config.SENSITIVE_MARKERS)


def find_timestamps(text: str) -> list[str]:
    return TIMESTAMP_RE.findall(text)


def find_entities(text: str, entities: list[dict]) -> list[dict]:
    low = text.lower()
    hits = []
    for e in entities:
        names = [e["name"].lower(), *[a.lower() for a in e.get("aliases", [])]]
        if any(_word_in(n, low) for n in names):
            hits.append(e)
    return hits


def _word_in(needle: str, haystack: str) -> bool:
    # word-ish boundary match so "sam" doesn't match "same"
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack) \
        is not None


def _confidence(scores: list[DestinationScore]) -> tuple[float, bool]:
    """Return (confidence, ambiguous)."""
    if not scores:
        return 0.0, False
    ranked = sorted(scores, key=lambda s: s.total, reverse=True)
    top = ranked[0].total
    second = ranked[1].total if len(ranked) > 1 else 0.0
    conf = min(1.0, top)
    ambiguous = (top - second) < config.settings.ambiguity_margin and second > 0.2
    if ambiguous:
        conf *= 0.6
    return round(conf, 3), ambiguous


def _section_for(dest_key: str, text: str) -> str:
    low = text.lower()
    if dest_key == "family" and any(k in low for k in
                                    ("shoe", "feet", "size", "clothing")):
        return "Clothing and sizes"
    if dest_key == "podcasts":
        return "Notes"
    if dest_key == "health":
        return "Log"
    return "Notes"


def _proposed_line(dest_key: str, text: str, timestamps: list[str]) -> str:
    today = date.today().isoformat()
    clean = text.strip().replace("\n", " ")
    if dest_key == "podcasts" and timestamps:
        ts = timestamps[0]
        # strip a leading timestamp from the body to avoid duplication
        body = TIMESTAMP_RE.sub("", clean, count=1).strip(" -—:")
        return f"{ts} — {body}"
    return f"{today}: {clean}"


def _default_note_path(dest_key: str) -> str:
    folder = config.DESTINATIONS_BY_KEY[dest_key].folder
    return f"{folder}/{dest_key}.md"


def apply_policy(capture_id: str, text: str, scores: list[DestinationScore],
                 ctx: ClassifierContext, *, score_signals: dict) -> Decision:
    """Turn scores + signals into a routed, explained Decision."""
    entities = score_signals.get("entities", [])
    timestamps = score_signals.get("timestamps", [])
    is_task = score_signals.get("is_task", False)
    is_sensitive = score_signals.get("is_sensitive", False)
    example_match = score_signals.get("example_match")  # dict or None

    confidence, ambiguous = _confidence(scores)
    ranked = sorted(scores, key=lambda s: s.total, reverse=True)
    top = ranked[0] if ranked else None
    top_key = top.destination_key if top else config.UNKNOWN_KEY

    entity_hit = entities[0] if entities else None
    example_strong = bool(example_match and example_match.get("similarity", 0) >= 0.5)

    # --- choose target + proposed action --------------------------------
    if entity_hit:
        note_path = entity_hit["note_path"]
        dest_key = entity_hit["destination_key"]
    elif example_strong and example_match.get("note_path"):
        note_path = example_match["note_path"]
        dest_key = example_match["destination_key"]
    else:
        dest_key = top_key
        note_path = _default_note_path(dest_key) if dest_key != config.UNKNOWN_KEY \
            else None

    exists = bool(note_path) and ctx.note_exists(note_path)
    proposed_action = Action.APPEND if exists else Action.CREATE
    section = _section_for(dest_key, text) if dest_key != config.UNKNOWN_KEY else None
    proposed_content = _proposed_line(dest_key, text, timestamps) \
        if dest_key != config.UNKNOWN_KEY else text.strip()

    # --- ask rules ------------------------------------------------------
    ask: list[str] = []
    if confidence < config.settings.low_confidence:
        ask.append("Confidence is below the auto-sort threshold.")
    elif confidence < config.settings.auto_confidence:
        ask.append("Confidence is moderate; a quick confirmation is safer.")
    if ambiguous:
        ask.append("Two or more destinations scored almost equally.")
    if proposed_action == Action.CREATE and dest_key != config.UNKNOWN_KEY \
            and config.DESTINATIONS_BY_KEY[dest_key].long_lived \
            and confidence < config.settings.auto_confidence:
        ask.append("This would create a new long-lived note.")

    hard: list[str] = []
    if is_task:
        hard.append("Looks like a task/reminder rather than knowledge.")
    if is_sensitive and not entity_hit:
        hard.append("Contains sensitive info with no clear destination.")

    # "Do not ask when ... a similar correction/example already exists" and the
    # destination is obvious (entity hit). Hard reasons (task/sensitive) survive.
    if example_strong or entity_hit:
        ask = []
    ask_reasons = hard + ask

    # --- final decision -------------------------------------------------
    if is_task:
        decision = Action.ASK
        needs_confirm = True
        reason = ("Phrasing reads like an action item; kept in inbox for you to "
                  "place or schedule.")
    elif (confidence < config.settings.low_confidence
          and not (entity_hit or example_strong)) or dest_key == config.UNKNOWN_KEY:
        decision = Action.REVIEW
        needs_confirm = True
        reason = "No destination scored confidently enough to route automatically."
        note_path, section, proposed_content = None, None, text.strip()
    else:
        decision = proposed_action
        needs_confirm = bool(ask_reasons)
        reason = _build_reason(top, entity_hit, example_match, proposed_action,
                               note_path)

    return Decision(
        capture_id=capture_id,
        decision=decision,
        confidence=confidence,
        destination=note_path,
        destination_key=(dest_key if dest_key != config.UNKNOWN_KEY else None),
        reason=reason,
        proposed_content=proposed_content,
        section=section,
        needs_user_confirmation=needs_confirm,
        ask_reasons=ask_reasons,
        scores=ranked,
        signals={
            "is_task": is_task,
            "is_sensitive": is_sensitive,
            "ambiguous": ambiguous,
            "timestamps": timestamps,
            "entities": [e["name"] for e in entities],
            "example_match": example_match,
            "podcast_session": score_signals.get("podcast_session"),
        },
    )


def _build_reason(top: Optional[DestinationScore], entity_hit, example_match,
                  action: Action, note_path: Optional[str]) -> str:
    bits = []
    if entity_hit:
        bits.append(f"Matched known entity '{entity_hit['name']}'")
    if example_match and example_match.get("similarity", 0) >= 0.5:
        bits.append(f"resembles a saved correction ({example_match['similarity']:.0%})")
    if top and not entity_hit:
        bits.append(f"top category '{top.label}' (score {top.total:.2f})")
    verb = "append to" if action == Action.APPEND else "create"
    where = note_path or "a new note"
    return f"{'; '.join(bits) or 'Best keyword match'}. Will {verb} {where}."


def merge_keyword_scores(text: str) -> dict[str, list[MatcherScore]]:
    """Keyword matcher shared by rule and ensemble backends."""
    low = text.lower()
    out: dict[str, list[MatcherScore]] = {}
    for dest in config.DESTINATIONS:
        hits = [kw for kw in dest.keywords if kw.strip() in low]
        if hits:
            score = min(0.6, 0.18 * len(hits))
            out.setdefault(dest.key, []).append(MatcherScore(
                matcher="keyword",
                destination_key=dest.key,
                score=round(score, 3),
                explanation=f"matched {len(hits)} keyword(s): {', '.join(hits[:4])}",
            ))
    return out
