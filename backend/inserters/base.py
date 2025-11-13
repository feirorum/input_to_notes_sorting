from abc import ABC, abstractmethod
from models.note import Note
from models.snippet import Snippet
from typing import Tuple


class BaseInserter(ABC):
    """Base class for insertion strategies"""

    @abstractmethod
    def insert(self, snippet: Snippet, note: Note) -> Tuple[str, dict]:
        """Insert snippet into note

        Args:
            snippet: Snippet to insert
            note: Note to insert into

        Returns:
            Tuple of (modified_content, undo_info)
            - modified_content: The new note content
            - undo_info: Information needed to undo this operation
        """
        pass
