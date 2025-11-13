from typing import List
import re
from .base import BaseMatcher
from models.note import Note
from models.snippet import Snippet


class StructureMatcher(BaseMatcher):
    """Matches based on structural patterns in notes and snippets"""

    def __init__(self):
        super().__init__()

    def detect_snippet_pattern(self, snippet: Snippet) -> str:
        """Detect the structural pattern of the snippet"""
        content = snippet.content

        # Check for various patterns
        if re.match(r'^-\s+\w+:', content):  # "- Name: Value"
            return "name_value_list"
        elif re.match(r'^\w+:\s+\d+', content):  # "Name: Number"
            return "key_number"
        elif re.match(r'^\[[\d:]+\]', content):  # "[12:34] note"
            return "timestamped_note"
        elif re.match(r'(?i)^(todo|task|reminder):', content):  # "TODO: ..."
            return "task_item"
        elif re.match(r'(?i)^(expense|receipt|paid):', content):  # "Expense: ..."
            return "expense_item"
        elif re.match(r'^\d{4}-\d{2}-\d{2}', content):  # "2025-01-13"
            return "dated_entry"
        elif re.search(r'```\w+', content):  # Code blocks
            return "code_snippet"
        elif re.match(r'^-\s+\[[ x]\]', content):  # "- [ ] task"
            return "checkbox_item"
        else:
            return "unstructured"

    def detect_note_patterns(self, note: Note) -> set:
        """Detect structural patterns present in a note"""
        patterns = set()

        lines = note.content.split('\n')
        for line in lines:
            if re.match(r'^-\s+\w+:\s+\d+', line):  # "- Name: Number"
                patterns.add("name_value_list")
            if re.match(r'^\[[\d:]+\]', line):  # "[12:34] note"
                patterns.add("timestamped_note")
            if re.match(r'^-\s+\[[ x]\]', line):  # "- [ ] task"
                patterns.add("checkbox_item")
            if re.search(r'```\w+', line):  # Code blocks
                patterns.add("code_snippet")
            if re.match(r'^\d{4}-\d{2}-\d{2}', line):  # Dates
                patterns.add("dated_entry")
            if re.match(r'^-\s+', line):  # Bullet points
                patterns.add("bullet_list")
            if re.match(r'^\d+\.', line):  # Numbered lists
                patterns.add("numbered_list")

        return patterns

    def match(self, snippet: Snippet, notes: List[Note]) -> dict[str, float]:
        """Match based on structural similarity"""
        snippet_pattern = self.detect_snippet_pattern(snippet)
        scores = {}

        for note in notes:
            note_patterns = self.detect_note_patterns(note)

            score = 0.0

            # Direct pattern match
            if snippet_pattern in note_patterns:
                score = 0.85

            # Special case: name_value_list pattern
            if snippet_pattern == "name_value_list":
                # Check if snippet content resembles existing lines in note
                snippet_lower = snippet.content.lower()
                # Look for similar patterns in content
                for line in note.content.split('\n'):
                    if re.match(r'^-\s+\w+:\s+\d+', line):
                        # Found similar structure
                        score = max(score, 0.9)
                        break

            # Timestamped notes should match media notes
            if snippet_pattern == "timestamped_note":
                if "timestamped_note" in note_patterns:
                    score = max(score, 0.85)

            # Task items should match checkbox lists
            if snippet_pattern == "task_item":
                if "checkbox_item" in note_patterns or "bullet_list" in note_patterns:
                    score = max(score, 0.75)

            # Expense items should match similar structure
            if snippet_pattern == "expense_item":
                # Check for financial/expense-related patterns in note
                if any(word in note.content.lower() for word in ['expense', 'receipt', 'paid', '$', 'bill']):
                    score = max(score, 0.8)

            # Code snippets should match notes with code blocks
            if snippet_pattern == "code_snippet":
                if "code_snippet" in note_patterns:
                    score = max(score, 0.85)

            # Bonus for notes with any matching patterns
            matching_patterns = len(note_patterns)
            if matching_patterns > 0:
                score = max(score, 0.3 + (0.05 * matching_patterns))

            scores[note.id] = self.normalize_score(score)

        return scores
