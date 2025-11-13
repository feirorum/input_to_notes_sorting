from typing import List, Dict
from models.note import Note
from models.snippet import Snippet
from models.match import Match, MatchResult, InsertionStrategy
from matchers.base import BaseMatcher


class ScoreAggregator:
    """Aggregates scores from multiple matchers"""

    def __init__(self, matchers: List[BaseMatcher]):
        """Initialize with list of matchers

        Args:
            matchers: List of matcher instances to use
        """
        self.matchers = matchers

    def aggregate_scores(
        self,
        snippet: Snippet,
        notes: List[Note]
    ) -> MatchResult:
        """Run all matchers and aggregate results

        Args:
            snippet: Input snippet to match
            notes: List of notes to match against

        Returns:
            MatchResult with sorted matches
        """
        # Collect scores from all matchers
        all_matcher_scores: Dict[str, Dict[str, float]] = {}

        for matcher in self.matchers:
            matcher_name = matcher.name
            scores = matcher.match(snippet, notes)
            all_matcher_scores[matcher_name] = scores

        # Aggregate scores for each note
        note_matches = []

        for note in notes:
            # Collect this note's scores from all matchers
            matcher_scores = {}
            for matcher_name, scores in all_matcher_scores.items():
                matcher_scores[matcher_name] = scores.get(note.id, 0.0)

            # Calculate weighted final score
            final_score = self.calculate_weighted_score(matcher_scores, snippet)

            # Skip notes with very low scores
            if final_score < 0.05:
                continue

            # Determine insertion strategy
            insertion_strategy = self.determine_insertion_strategy(
                snippet, note, matcher_scores
            )

            # Generate preview
            preview = self.generate_preview(snippet, note, insertion_strategy)

            # Generate reasoning
            reasoning = self.generate_reasoning(matcher_scores, note)

            # Create match object
            match = Match(
                note_id=note.id,
                note_title=note.title,
                section=None,  # TODO: Detect specific section
                matcher_scores=matcher_scores,
                final_score=final_score,
                insertion_strategy=insertion_strategy,
                preview=preview,
                confidence=Match.determine_confidence(final_score),
                reasoning=reasoning
            )

            note_matches.append(match)

        # Sort by final score (descending)
        note_matches.sort(key=lambda m: m.final_score, reverse=True)

        # Determine if manual review is needed
        requires_manual_review = self.check_manual_review_needed(note_matches)

        # Get top recommendation
        recommendation = note_matches[0] if note_matches else None

        return MatchResult(
            matches=note_matches,
            recommendation=recommendation,
            requires_manual_review=requires_manual_review,
            reasoning=self.generate_overall_reasoning(note_matches, requires_manual_review)
        )

    def calculate_weighted_score(
        self,
        matcher_scores: Dict[str, float],
        snippet: Snippet
    ) -> float:
        """Calculate weighted final score from matcher scores

        Weights are adjusted based on snippet characteristics
        """
        # Default weights
        weights = {
            "keyword": 0.25,
            "structure": 0.20,
            "entity": 0.20,
            "context": 0.25,
            "project": 0.10
        }

        # Adjust weights based on snippet characteristics
        if snippet.has_media_context():
            # For media snippets, context matching is more important
            weights["context"] = 0.40
            weights["keyword"] = 0.20
            weights["structure"] = 0.15
            weights["entity"] = 0.15
            weights["project"] = 0.10

        # Calculate weighted sum
        total_score = 0.0
        total_weight = 0.0

        for matcher_name, score in matcher_scores.items():
            weight = weights.get(matcher_name, 0.1)
            total_score += score * weight
            total_weight += weight

        # Normalize by total weight
        if total_weight > 0:
            return total_score / total_weight
        return 0.0

    def determine_insertion_strategy(
        self,
        snippet: Snippet,
        note: Note,
        matcher_scores: Dict[str, float]
    ) -> InsertionStrategy:
        """Determine best insertion strategy based on content and scores"""

        # High structure score suggests APPEND to existing list
        if matcher_scores.get("structure", 0) > 0.75:
            return InsertionStrategy.APPEND

        # Media context suggests APPEND with timestamp
        if snippet.has_media_context() and matcher_scores.get("context", 0) > 0.7:
            return InsertionStrategy.APPEND

        # High keyword/entity overlap suggests MERGE
        if (matcher_scores.get("keyword", 0) > 0.7 or
            matcher_scores.get("entity", 0) > 0.7):
            return InsertionStrategy.MERGE

        # Default to APPEND
        return InsertionStrategy.APPEND

    def generate_preview(
        self,
        snippet: Snippet,
        note: Note,
        strategy: InsertionStrategy
    ) -> str:
        """Generate preview of how snippet would be inserted"""

        if strategy == InsertionStrategy.APPEND:
            # Show what would be appended
            if snippet.has_media_context():
                timestamp = snippet.get_media_timestamp()
                return f"[{timestamp}] {snippet.content}"
            else:
                return f"- {snippet.content} ({snippet.timestamp.strftime('%Y-%m-%d')})"

        elif strategy == InsertionStrategy.MERGE:
            return f"Merge into relevant section: {snippet.content[:100]}..."

        elif strategy == InsertionStrategy.LINK:
            return f"Add as reference: {snippet.content[:100]}..."

        return snippet.content[:100]

    def generate_reasoning(
        self,
        matcher_scores: Dict[str, float],
        note: Note
    ) -> str:
        """Generate human-readable reasoning for the match"""

        # Find top scoring matchers
        sorted_matchers = sorted(
            matcher_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        reasons = []

        for matcher_name, score in sorted_matchers[:3]:
            if score > 0.5:
                if matcher_name == "keyword":
                    reasons.append("Strong keyword match")
                elif matcher_name == "structure":
                    reasons.append("Similar structure detected")
                elif matcher_name == "entity":
                    reasons.append("Matching entities found")
                elif matcher_name == "context":
                    reasons.append("Matching media context")
                elif matcher_name == "project":
                    reasons.append("Project reference match")

        if not reasons:
            return "Low confidence match"

        return ", ".join(reasons)

    def check_manual_review_needed(self, matches: List[Match]) -> bool:
        """Check if manual review is needed

        Manual review needed if:
        - No high-confidence matches
        - Multiple matches with similar scores (within 0.1)
        - Top match has medium/low confidence
        """
        if not matches:
            return True

        top_match = matches[0]

        # Low confidence on top match
        if top_match.confidence != "high":
            return True

        # Check for multiple close matches
        close_matches = [
            m for m in matches
            if top_match.final_score - m.final_score <= 0.1
        ]

        if len(close_matches) > 1:
            return True

        return False

    def generate_overall_reasoning(
        self,
        matches: List[Match],
        requires_manual_review: bool
    ) -> str:
        """Generate overall reasoning for the match result"""

        if not matches:
            return "No suitable matches found. Consider creating a new note."

        if requires_manual_review:
            return "Multiple potential matches found. Manual review recommended."

        top_match = matches[0]
        return f"High confidence match to '{top_match.note_title}'"
