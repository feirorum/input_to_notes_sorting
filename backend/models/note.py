from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime


class Note(BaseModel):
    """Represents a note in the knowledge base"""

    id: str
    title: str
    content: str
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None

    def __str__(self) -> str:
        return f"Note({self.id}: {self.title})"

    def get_sections(self) -> List[tuple[str, str]]:
        """Parse markdown content into sections

        Returns:
            List of (heading, content) tuples
        """
        sections = []
        current_heading = "Root"
        current_content = []

        for line in self.content.split('\n'):
            if line.startswith('#'):
                if current_content:
                    sections.append((current_heading, '\n'.join(current_content)))
                current_heading = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections.append((current_heading, '\n'.join(current_content)))

        return sections

    def find_section(self, section_name: str) -> Optional[tuple[int, int]]:
        """Find a section by name and return its line range

        Args:
            section_name: Name of the section to find

        Returns:
            Tuple of (start_line, end_line) or None if not found
        """
        lines = self.content.split('\n')
        start_line = None

        for i, line in enumerate(lines):
            if line.startswith('#') and section_name.lower() in line.lower():
                start_line = i
                break

        if start_line is None:
            return None

        # Find end of section (next heading or end of file)
        end_line = len(lines)
        for i in range(start_line + 1, len(lines)):
            if lines[i].startswith('#'):
                end_line = i
                break

        return (start_line, end_line)
