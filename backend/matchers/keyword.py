from typing import List
from .base import BaseMatcher
from models.note import Note
from models.snippet import Snippet
import re


class KeywordMatcher(BaseMatcher):
    """Matches based on keyword overlap between snippet and notes"""

    def __init__(self):
        super().__init__()
        # Common words to ignore
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'this', 'that', 'they', 'them',
            'i', 'me', 'my', 'we', 'our', 'you', 'your'
        }

    def extract_keywords(self, text: str) -> set:
        """Extract keywords from text"""
        # Convert to lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out stop words and short words
        keywords = {w for w in words if w not in self.stop_words and len(w) > 2}
        return keywords

    def extract_phrases(self, text: str) -> set:
        """Extract 2-3 word phrases"""
        words = re.findall(r'\b\w+\b', text.lower())
        phrases = set()

        # 2-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if words[i] not in self.stop_words or words[i+1] not in self.stop_words:
                phrases.add(phrase)

        # 3-word phrases
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            phrases.add(phrase)

        return phrases

    def match(self, snippet: Snippet, notes: List[Note]) -> dict[str, float]:
        """Match based on keyword and phrase overlap"""
        snippet_keywords = self.extract_keywords(snippet.content)
        snippet_phrases = self.extract_phrases(snippet.content)

        scores = {}

        for note in notes:
            # Combine title, content, and tags for matching
            note_text = f"{note.title} {note.content} {' '.join(note.tags)}"
            note_keywords = self.extract_keywords(note_text)
            note_phrases = self.extract_phrases(note_text)

            # Calculate phrase matches (weighted higher)
            phrase_matches = snippet_phrases & note_phrases
            phrase_score = len(phrase_matches) * 0.3  # Each phrase match worth 0.3

            # Calculate keyword matches
            keyword_matches = snippet_keywords & note_keywords
            keyword_score = len(keyword_matches) * 0.1  # Each keyword worth 0.1

            # Check for exact phrase matches in note (even higher weight)
            exact_matches = 0
            for phrase in snippet_phrases:
                if phrase in note_text.lower():
                    exact_matches += 1

            exact_score = exact_matches * 0.4

            # Combine scores
            total_score = phrase_score + keyword_score + exact_score

            scores[note.id] = self.normalize_score(total_score)

        return scores
