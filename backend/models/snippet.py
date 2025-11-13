from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime


class Snippet(BaseModel):
    """Represents an input snippet to be sorted"""

    id: Optional[str] = None
    content: str
    source: str  # "manual", "podcast", "youtube", "web_clipper", etc.
    timestamp: datetime
    metadata: Dict[str, Any] = {}

    def __str__(self) -> str:
        return f"Snippet({self.source}: {self.content[:50]}...)"

    def has_media_context(self) -> bool:
        """Check if snippet has media context (URL, timestamp in media)"""
        return "url" in self.metadata and "timestamp_in_media" in self.metadata

    def get_media_url(self) -> Optional[str]:
        """Get media URL if available"""
        return self.metadata.get("url")

    def get_media_timestamp(self) -> Optional[str]:
        """Get timestamp within media (e.g., '15:23')"""
        return self.metadata.get("timestamp_in_media")

    def get_media_duration_minutes(self) -> Optional[int]:
        """Get media duration in minutes"""
        return self.metadata.get("media_duration_minutes")

    def get_media_start_time(self) -> Optional[datetime]:
        """Get the start time when media was played/listened"""
        start_time_str = self.metadata.get("media_start_time")
        if start_time_str:
            if isinstance(start_time_str, datetime):
                return start_time_str
            return datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        return None
