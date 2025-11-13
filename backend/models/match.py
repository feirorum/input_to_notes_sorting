from pydantic import BaseModel
from typing import Dict, Optional, List
from enum import Enum


class InsertionStrategy(str, Enum):
    """Types of insertion strategies"""
    APPEND = "APPEND"
    MERGE = "MERGE"
    LINK = "LINK"
    CREATE_SECTION = "CREATE_SECTION"
    CREATE_NEW = "CREATE_NEW"


class ConfidenceLevel(str, Enum):
    """Confidence levels for matches"""
    HIGH = "high"  # >= 0.8
    MEDIUM = "medium"  # 0.5 - 0.79
    LOW = "low"  # < 0.5


class Match(BaseModel):
    """Represents a single match between snippet and note"""

    note_id: str
    note_title: str
    section: Optional[str] = None
    matcher_scores: Dict[str, float]  # {matcher_name: score}
    final_score: float
    insertion_strategy: InsertionStrategy
    preview: str  # Preview of the change
    confidence: ConfidenceLevel
    reasoning: str  # Human-readable explanation

    @classmethod
    def determine_confidence(cls, score: float) -> ConfidenceLevel:
        """Determine confidence level based on score"""
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


class MatchResult(BaseModel):
    """Complete result of matching process"""

    matches: List[Match]
    recommendation: Optional[Match] = None
    requires_manual_review: bool = False
    reasoning: str = ""

    def get_top_match(self) -> Optional[Match]:
        """Get the highest scoring match"""
        if not self.matches:
            return None
        return max(self.matches, key=lambda m: m.final_score)

    def get_close_matches(self, threshold: float = 0.1) -> List[Match]:
        """Get matches that are within threshold of top score

        Args:
            threshold: Maximum score difference to consider "close"

        Returns:
            List of matches within threshold of top match
        """
        if not self.matches:
            return []

        top_score = self.matches[0].final_score
        return [m for m in self.matches if top_score - m.final_score <= threshold]
