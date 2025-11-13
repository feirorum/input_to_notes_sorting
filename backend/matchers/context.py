from typing import List
from datetime import datetime, timedelta
from .base import BaseMatcher
from models.note import Note
from models.snippet import Snippet


class ContextMatcher(BaseMatcher):
    """Matches based on context: URLs, timestamps, media information"""

    def __init__(self):
        super().__init__()

    def parse_timestamp_to_seconds(self, timestamp_str: str) -> int:
        """Parse timestamp like '15:23' or '1:05:30' to seconds

        Args:
            timestamp_str: Timestamp string in format MM:SS or HH:MM:SS

        Returns:
            Total seconds
        """
        parts = timestamp_str.split(':')
        parts = [int(p) for p in parts]

        if len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return 0

    def calculate_time_match_score(
        self,
        snippet_timestamp: datetime,
        media_start_time: datetime,
        media_duration_minutes: int,
        snippet_media_timestamp: str,
        note_created_at: datetime,
        note_updated_at: datetime
    ) -> float:
        """Calculate time-based match score with gradual scoring

        Rules:
        - 5 minutes before media start: gradual score increase
        - During media playback: high score (1.0)
        - 20 minutes after media end: gradual score decrease
        - Outside this window: very low score

        Args:
            snippet_timestamp: When the snippet was created
            media_start_time: When media playback started
            media_duration_minutes: Length of media in minutes
            snippet_media_timestamp: Position in media (e.g., "15:23")
            note_created_at: When note was created
            note_updated_at: When note was last updated

        Returns:
            Score from 0.0 to 1.0
        """
        # Calculate media end time
        media_end_time = media_start_time + timedelta(minutes=media_duration_minutes)

        # Calculate window boundaries
        window_start = media_start_time - timedelta(minutes=5)  # 5 min before
        window_end = media_end_time + timedelta(minutes=20)  # 20 min after

        # Check if snippet timestamp is in the window
        if snippet_timestamp < window_start or snippet_timestamp > window_end:
            return 0.0

        # Calculate position within window
        if window_start <= snippet_timestamp <= media_start_time:
            # 5 minutes before start: gradual increase
            # Linear interpolation from 0.3 to 1.0
            time_diff = (snippet_timestamp - window_start).total_seconds()
            max_diff = (media_start_time - window_start).total_seconds()
            progress = time_diff / max_diff if max_diff > 0 else 0
            return 0.3 + (0.7 * progress)

        elif media_start_time <= snippet_timestamp <= media_end_time:
            # During playback: full score
            return 1.0

        elif media_end_time < snippet_timestamp <= window_end:
            # 20 minutes after end: gradual decrease
            # Linear interpolation from 1.0 to 0.5
            time_diff = (snippet_timestamp - media_end_time).total_seconds()
            max_diff = (window_end - media_end_time).total_seconds()
            progress = time_diff / max_diff if max_diff > 0 else 0
            return 1.0 - (0.5 * progress)

        return 0.0

    def check_url_match(self, snippet_url: str, note_metadata: dict) -> bool:
        """Check if URLs match"""
        if not snippet_url or not note_metadata:
            return False

        note_url = note_metadata.get("url", "")
        return snippet_url == note_url

    def check_timestamp_in_media_range(
        self,
        snippet_media_timestamp: str,
        media_duration_minutes: int
    ) -> bool:
        """Check if timestamp is within valid media range"""
        timestamp_seconds = self.parse_timestamp_to_seconds(snippet_media_timestamp)
        media_duration_seconds = media_duration_minutes * 60

        # Allow some overflow (people might note a bit after media ends)
        return timestamp_seconds <= media_duration_seconds + 300  # +5 minutes buffer

    def match(self, snippet: Snippet, notes: List[Note]) -> dict[str, float]:
        """Match based on media context and timestamps"""
        scores = {}

        # If snippet doesn't have media context, return zeros
        if not snippet.has_media_context():
            return {note.id: 0.0 for note in notes}

        snippet_url = snippet.get_media_url()
        snippet_media_timestamp = snippet.get_media_timestamp()
        snippet_duration = snippet.get_media_duration_minutes()
        snippet_start_time = snippet.get_media_start_time()

        for note in notes:
            score = 0.0

            # Check URL match first
            if note.metadata and self.check_url_match(snippet_url, note.metadata):
                score += 0.5  # Base score for URL match

                # If we have time information, calculate time-based score
                if (snippet_start_time and
                    snippet_duration and
                    note.metadata.get("listened_at") or note.metadata.get("watched_at")):

                    # Get note's media start time
                    note_media_start = note.metadata.get("listened_at") or note.metadata.get("watched_at")
                    if isinstance(note_media_start, str):
                        note_media_start = datetime.fromisoformat(note_media_start.replace('Z', '+00:00'))

                    note_duration = note.metadata.get("duration_minutes", snippet_duration)

                    # Calculate time match score
                    time_score = self.calculate_time_match_score(
                        snippet.timestamp,
                        snippet_start_time,
                        snippet_duration,
                        snippet_media_timestamp,
                        note.created_at,
                        note.updated_at
                    )

                    # Combine URL match with time match
                    # URL match (0.5) + time match (0.5 max) = 1.0 max
                    score = 0.5 + (time_score * 0.5)

                    # Verify timestamp is within media range
                    if snippet_media_timestamp:
                        if not self.check_timestamp_in_media_range(
                            snippet_media_timestamp,
                            snippet_duration
                        ):
                            # Timestamp is beyond media duration, reduce score
                            score *= 0.5

            scores[note.id] = self.normalize_score(score)

        return scores
