from typing import List
import re
from .base import BaseMatcher
from models.note import Note
from models.snippet import Snippet


class ProjectMatcher(BaseMatcher):
    """Matches based on project references"""

    def __init__(self):
        super().__init__()

    def extract_project_names(self, text: str) -> set:
        """Extract project names from text

        Looks for patterns like:
        - "XYZ project"
        - "Project ABC"
        - "the XYZ project"
        - "on the ABC project"
        """
        project_names = set()

        # Various patterns for project mentions
        patterns = [
            r'\b([A-Z][A-Z0-9]+)\s+project\b',  # "XYZ project"
            r'\bproject\s+([A-Z][A-Za-z0-9]+)\b',  # "Project ABC"
            r'\bthe\s+([A-Z][A-Za-z0-9]+)\s+project\b',  # "the ABC project"
            r'\bon\s+the\s+([A-Z][A-Za-z0-9]+)\s+project\b',  # "on the ABC project"
            r'\bfor\s+the\s+([A-Z][A-Za-z0-9]+)\s+project\b',  # "for the ABC project"
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                project_name = match.group(1)
                project_names.add(project_name.upper())

        return project_names

    def check_title_project_match(self, project_names: set, note_title: str) -> bool:
        """Check if note title contains project reference"""
        title_upper = note_title.upper()

        for project in project_names:
            if project in title_upper:
                return True

        return False

    def match(self, snippet: Snippet, notes: List[Note]) -> dict[str, float]:
        """Match based on project references"""
        snippet_projects = self.extract_project_names(snippet.content)

        scores = {}

        for note in notes:
            score = 0.0

            # If snippet mentions projects
            if snippet_projects:
                # Check title match (strongest signal)
                if self.check_title_project_match(snippet_projects, note.title):
                    score += 0.9

                # Check content match
                note_projects = self.extract_project_names(note.content)
                matching_projects = snippet_projects & note_projects

                if matching_projects:
                    # Each matching project adds to score
                    score += min(0.7, len(matching_projects) * 0.35)

                # Check tags
                note_tags_upper = {tag.upper() for tag in note.tags}
                if snippet_projects & note_tags_upper:
                    score += 0.3

            # Even without explicit "project" keyword, check for capitalized
            # identifiers that might be project names
            snippet_words = re.findall(r'\b[A-Z][A-Z0-9]{2,}\b', snippet.content)
            if snippet_words:
                title_upper = note.title.upper()
                for word in snippet_words:
                    if word in title_upper:
                        score += 0.5
                        break

            scores[note.id] = self.normalize_score(score)

        return scores
