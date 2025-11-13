from typing import List, Set
import re
from .base import BaseMatcher
from models.note import Note
from models.snippet import Snippet


class EntityMatcher(BaseMatcher):
    """Matches based on named entities (people, projects, places)"""

    def __init__(self):
        super().__init__()

    def extract_entities(self, text: str) -> dict[str, Set[str]]:
        """Extract entities from text

        Returns:
            Dictionary with entity types as keys and sets of entities as values
        """
        entities = {
            "people": set(),
            "projects": set(),
            "technical": set(),
        }

        # Extract capitalized names (potential people/places)
        # Look for capitalized words that aren't at start of sentence
        words = text.split()
        for i, word in enumerate(words):
            # Remove punctuation for checking
            clean_word = re.sub(r'[^\w]', '', word)

            if clean_word and clean_word[0].isupper() and len(clean_word) > 1:
                # Skip if it's the first word (might be sentence start)
                if i > 0 or word == clean_word:
                    # Check if it's not a common word that's capitalized
                    if clean_word.lower() not in {'the', 'a', 'an', 'i'}:
                        entities["people"].add(clean_word)

        # Extract project references
        # Look for patterns like "XYZ project", "Project ABC", "the ABC project"
        project_patterns = [
            r'\b([A-Z][A-Z0-9]+)\s+project\b',
            r'\bproject\s+([A-Z][A-Za-z0-9]+)\b',
            r'\bthe\s+([A-Z][A-Za-z0-9]+)\s+project\b'
        ]

        for pattern in project_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities["projects"].add(match.group(1))

        # Extract technical terms (common frameworks, languages, tools)
        technical_terms = {
            'python', 'javascript', 'java', 'rust', 'go', 'typescript',
            'react', 'vue', 'angular', 'django', 'flask', 'fastapi',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp',
            'postgres', 'mongodb', 'redis', 'mysql',
            'git', 'github', 'gitlab',
            'api', 'rest', 'graphql',
            'ml', 'ai', 'nlp'
        }

        text_lower = text.lower()
        for term in technical_terms:
            if re.search(r'\b' + term + r'\b', text_lower):
                entities["technical"].add(term)

        return entities

    def calculate_entity_overlap(self, entities1: dict, entities2: dict) -> float:
        """Calculate overlap score between two entity dictionaries"""
        total_score = 0.0
        weights = {
            "people": 0.4,
            "projects": 0.5,
            "technical": 0.3
        }

        for entity_type, weight in weights.items():
            set1 = entities1.get(entity_type, set())
            set2 = entities2.get(entity_type, set())

            if not set1:
                continue

            # Calculate Jaccard similarity
            intersection = len(set1 & set2)
            union = len(set1 | set2)

            if union > 0:
                similarity = intersection / union
                total_score += similarity * weight

        return total_score

    def match(self, snippet: Snippet, notes: List[Note]) -> dict[str, float]:
        """Match based on entity overlap"""
        snippet_entities = self.extract_entities(snippet.content)
        scores = {}

        for note in notes:
            # Extract entities from note (title, content, tags)
            note_text = f"{note.title} {note.content} {' '.join(note.tags)}"
            note_entities = self.extract_entities(note_text)

            # Calculate overlap score
            score = self.calculate_entity_overlap(snippet_entities, note_entities)

            # Boost score if title contains a matching entity
            title_lower = note.title.lower()
            for entity_type in snippet_entities:
                for entity in snippet_entities[entity_type]:
                    if entity.lower() in title_lower:
                        score += 0.3
                        break

            scores[note.id] = self.normalize_score(score)

        return scores
