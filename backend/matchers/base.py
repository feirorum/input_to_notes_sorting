from abc import ABC, abstractmethod
from typing import List
from models.note import Note
from models.snippet import Snippet


class BaseMatcher(ABC):
    """Base class for all matchers"""

    def __init__(self):
        self.name = self.__class__.__name__.replace("Matcher", "").lower()

    @abstractmethod
    def match(self, snippet: Snippet, notes: List[Note]) -> dict[str, float]:
        """Calculate match scores for snippet against all notes

        Args:
            snippet: Input snippet to match
            notes: List of notes to match against

        Returns:
            Dictionary mapping note_id to score (0.0-1.0)
        """
        pass

    def normalize_score(self, score: float) -> float:
        """Ensure score is between 0 and 1"""
        return max(0.0, min(1.0, score))

    def __str__(self) -> str:
        return self.name
