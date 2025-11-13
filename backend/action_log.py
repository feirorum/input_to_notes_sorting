from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.snippet import Snippet
from models.match import Match


class ActionLogEntry(BaseModel):
    """Represents a single sorting action"""

    id: str
    timestamp: datetime
    snippet_content: str
    snippet_source: str
    matched_note_id: str
    matched_note_title: str
    action: str  # "append", "merge", "link", "create"
    preview: str
    undo_info: Dict[str, Any]
    final_score: float
    was_manual_review: bool = False

    def get_summary(self) -> str:
        """Generate one-line summary for display"""
        action_emoji = {
            "append": "➕",
            "merge": "🔀",
            "link": "🔗",
            "create": "📝"
        }

        emoji = action_emoji.get(self.action, "📄")
        content_preview = self.snippet_content[:40]
        if len(self.snippet_content) > 40:
            content_preview += "..."

        return f"{emoji} {content_preview} → {self.matched_note_title}"


class ActionLog:
    """Manages sorting action history"""

    def __init__(self):
        self.entries: List[ActionLogEntry] = []
        self._next_id = 1

    def add_entry(
        self,
        snippet: Snippet,
        match: Match,
        undo_info: Dict[str, Any],
        was_manual_review: bool = False
    ) -> ActionLogEntry:
        """Add a new action to the log

        Args:
            snippet: The snippet that was sorted
            match: The match that was selected
            undo_info: Information needed to undo this action
            was_manual_review: Whether this required manual review

        Returns:
            The created log entry
        """
        entry = ActionLogEntry(
            id=f"action-{self._next_id}",
            timestamp=datetime.now(),
            snippet_content=snippet.content,
            snippet_source=snippet.source,
            matched_note_id=match.note_id,
            matched_note_title=match.note_title,
            action=match.insertion_strategy.value.lower(),
            preview=match.preview,
            undo_info=undo_info,
            final_score=match.final_score,
            was_manual_review=was_manual_review
        )

        self.entries.append(entry)
        self._next_id += 1

        return entry

    def get_recent(self, limit: int = 10) -> List[ActionLogEntry]:
        """Get most recent actions

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent entries (newest first)
        """
        return list(reversed(self.entries[-limit:]))

    def get_by_id(self, action_id: str) -> Optional[ActionLogEntry]:
        """Get action by ID

        Args:
            action_id: ID of action to retrieve

        Returns:
            Action entry or None if not found
        """
        for entry in self.entries:
            if entry.id == action_id:
                return entry
        return None

    def get_all(self) -> List[ActionLogEntry]:
        """Get all actions (newest first)"""
        return list(reversed(self.entries))


# Global action log instance
action_log = ActionLog()
