"""Pydantic / dataclass models shared across the system."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Action(str, Enum):
    APPEND = "append_to_existing_note"
    CREATE = "create_new_note"
    ASK = "leave_in_inbox_ask"
    REVIEW = "needs_review"


class CaptureStatus(str, Enum):
    NEW = "new"
    PROCESSED = "processed"
    NEEDS_REVIEW = "needs_review"
    PENDING = "pending"  # classified, awaiting user confirmation


class CaptureIn(BaseModel):
    text: str = Field(..., min_length=1)
    source: str = "manual"
    source_type: str = "quick_note"
    # Optional client-supplied capture time (e.g. when importing).
    created_at: Optional[str] = None


class Capture(BaseModel):
    id: str
    created_at: str
    source: str
    source_type: str
    status: CaptureStatus
    processed: bool
    text: str
    inbox_path: str


class MatcherScore(BaseModel):
    """One matcher's contribution to one destination, with a why."""
    matcher: str
    destination_key: str
    score: float
    explanation: str


class DestinationScore(BaseModel):
    destination_key: str
    label: str
    total: float
    contributions: list[MatcherScore] = []


class Decision(BaseModel):
    capture_id: str
    decision: Action
    confidence: float
    destination: Optional[str] = None  # vault-relative path of the target note
    destination_key: Optional[str] = None
    reason: str = ""
    proposed_content: str = ""
    section: Optional[str] = None  # heading the content goes under, if appending
    needs_user_confirmation: bool = False
    ask_reasons: list[str] = []
    # Full transparency for the demo middle pane:
    scores: list[DestinationScore] = []
    signals: dict[str, Any] = {}  # task?, sensitive?, entities, podcast session


class CorrectIn(BaseModel):
    destination_key: str
    action: Action = Action.APPEND
    note_path: Optional[str] = None  # if appending to a specific existing note
    new_note_title: Optional[str] = None  # if creating a new note
    save_example: bool = True


class AuditEntry(BaseModel):
    id: int
    capture_id: str
    processed_at: str
    action: str
    destination: Optional[str]
    confidence: float
    undo_available: bool
    undone: bool
    reasoning: str
    change_made: str
