"""Configuration: destinations, routing rules, known entities, thresholds.

Everything here is data, not behaviour. The classifier reads it; the demo UI
renders it. Keeping it in one place makes the matching logic auditable and lets
a future iteration move it into the vault (system/routing-rules.yaml) without
touching the matchers.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --- Paths -----------------------------------------------------------------
VAULT_DIR = Path(os.environ.get("VAULT_DIR", "vault")).resolve()
INBOX_DIR = VAULT_DIR / "inbox"
NOTES_DIR = VAULT_DIR / "notes"
SYSTEM_DIR = VAULT_DIR / "system"
AUDIT_DIR = VAULT_DIR / "audit-log"
DB_PATH = Path(os.environ.get("SORTER_DB", "sorter.db")).resolve()

# rules | llm | ensemble
CLASSIFIER = os.environ.get("CLASSIFIER", "rules")
LLM_MODEL = os.environ.get("LLM_MODEL", "claude-opus-4-8")

# --- Decision thresholds ---------------------------------------------------
# Below LOW_CONFIDENCE we never auto-act: the item goes to review / inbox.
# At or above AUTO_CONFIDENCE we act without asking (when the action is safe).
LOW_CONFIDENCE = 0.45
AUTO_CONFIDENCE = 0.70
# If the top two destinations are within this margin, treat it as ambiguous.
AMBIGUITY_MARGIN = 0.12


@dataclass(frozen=True)
class Destination:
    key: str           # short id, e.g. "family"
    label: str         # human label
    folder: str        # vault-relative folder, e.g. "notes/family"
    keywords: tuple[str, ...] = ()
    # If True, creating a *new* top-level note here is "long-lived" and the
    # agent should confirm before doing it (per spec ask-rules).
    long_lived: bool = True


DESTINATIONS: tuple[Destination, ...] = (
    Destination(
        "family", "Family / children records", "notes/family",
        keywords=("son", "daughter", "kid", "child", "shoe", "feet", "size",
                  "school", "clothing", "birthday", "doctor", "vaccination"),
    ),
    Destination(
        "podcasts", "Podcast notes", "notes/podcasts",
        keywords=("podcast", "episode", "listened", "host", "interview", "ep ",
                  "spotify", "audio"),
    ),
    Destination(
        "work", "Work ideas", "notes/work",
        keywords=("project", "meeting", "security", "deadline", "stakeholder",
                  "client", "sprint", "ticket", "copilot", "champions"),
    ),
    Destination(
        "learning", "AI / developer learning", "notes/learning",
        keywords=("ai", "llm", "model", "python", "code", "algorithm", "paper",
                  "tutorial", "context window", "embedding", "rag", "agent"),
    ),
    Destination(
        "projects", "Personal projects", "notes/projects",
        keywords=("build", "prototype", "side project", "garage", "repo",
                  "hobby", "3d print", "raspberry"),
    ),
    Destination(
        "health", "Health / sports", "notes/health",
        keywords=("run", "running", "gym", "workout", "weight", "sleep", "diet",
                  "injury", "heart rate", "steps", "calories"),
    ),
    Destination(
        "shopping", "Shopping / practical errands", "notes/shopping",
        keywords=("buy", "shopping", "groceries", "order", "errand", "pick up",
                  "store", "list", "milk", "batteries"),
    ),
    Destination(
        "references", "General reference", "notes/references",
        keywords=("reference", "link", "article", "quote", "fact", "how to",
                  "recipe", "address"),
    ),
)

DESTINATIONS_BY_KEY = {d.key: d for d in DESTINATIONS}

# Special pseudo-destinations (not knowledge categories).
UNKNOWN_KEY = "unknown"  # -> needs review


@dataclass
class Entity:
    """A known long-lived thing that maps to a specific note.

    Entity hits are the strongest routing signal: "Flora" reliably means the
    Flora note, regardless of keyword soup. The registry also lets the agent
    recognise when a capture would create a *new* entity (ask-rule trigger).
    """
    name: str
    destination_key: str
    note_path: str            # vault-relative file
    aliases: tuple[str, ...] = ()
    kind: str = "person"      # person | project | podcast


# Seeded so the demo "append to existing note" scenarios work out of the box.
ENTITIES: list[Entity] = [
    Entity("Flora", "family", "notes/family/flora.md",
           aliases=("flora's",), kind="person"),
    Entity("Sam", "family", "notes/family/sam.md",
           aliases=("sam's",), kind="person"),
    Entity("XYZ", "work", "notes/work/xyz-project.md",
           aliases=("xyz project", "project xyz"), kind="project"),
    Entity("Practical AI", "podcasts", "notes/podcasts/practical-ai.md",
           aliases=("practical ai podcast",), kind="podcast"),
]

# Phrases that suggest a task/reminder rather than a knowledge snippet.
TASK_MARKERS = (
    "remind me", "remember to", "todo", "to-do", "don't forget", "need to",
    "have to", "must ", "buy ", "call ", "email ", "schedule ", "book ",
    "pick up", "deadline", "by tomorrow", "by friday", "follow up",
)

# Phrases that suggest sensitive/private content.
SENSITIVE_MARKERS = (
    "password", "ssn", "social security", "diagnosis", "medication",
    "salary", "bank", "account number", "confidential", "private", "iban",
    "pin ", "credit card",
)

# Seed corrections so the example-similarity matcher has something to learn from
# and the demo can show corrections influencing scores. Mirrors the spec example.
SEED_EXAMPLES = [
    {
        "title": "child size notes",
        "text": "Flora's feet are now size 34.",
        "destination_key": "family",
        "note_path": "notes/family/flora.md",
        "note": ("Short family facts about a specific child go to that child's "
                 "family record, not to shopping."),
    },
]


@dataclass
class Settings:
    vault_dir: Path = field(default_factory=lambda: VAULT_DIR)
    classifier: str = CLASSIFIER
    llm_model: str = LLM_MODEL
    low_confidence: float = LOW_CONFIDENCE
    auto_confidence: float = AUTO_CONFIDENCE
    ambiguity_margin: float = AMBIGUITY_MARGIN


settings = Settings()
