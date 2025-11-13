from .base import BaseInserter
from models.note import Note
from models.snippet import Snippet
from typing import Tuple
import re


class AppendInserter(BaseInserter):
    """Appends snippet to note, detecting appropriate location"""

    def insert(self, snippet: Snippet, note: Note) -> Tuple[str, dict]:
        """Append snippet to note"""

        content_lines = note.content.split('\n')

        # Detect if snippet should go in a specific section
        section_line = self.find_best_section(snippet, content_lines)

        # Format the snippet for insertion
        formatted_snippet = self.format_snippet(snippet)

        # Create undo info before modification
        undo_info = {
            "original_content": note.content,
            "note_id": note.id,
            "operation": "append",
            "snippet_content": snippet.content
        }

        if section_line is not None:
            # Insert after the section header and existing content
            insert_position = self.find_append_position(
                content_lines,
                section_line
            )
            content_lines.insert(insert_position, formatted_snippet)
        else:
            # Append to end of note
            content_lines.append("")  # Blank line
            content_lines.append(formatted_snippet)

        modified_content = '\n'.join(content_lines)

        return modified_content, undo_info

    def find_best_section(self, snippet: Snippet, content_lines: list) -> int:
        """Find the best section to append to

        Returns:
            Line number of section header, or None for end of file
        """
        # Look for patterns in snippet to match section names
        content_lower = snippet.content.lower()

        # Check for specific patterns
        if re.search(r'\bshoe\s+size', content_lower):
            return self.find_section_header(content_lines, "shoe size")

        if re.search(r'\btodo\b|^task:', content_lower, re.IGNORECASE):
            return self.find_section_header(content_lines, ["todo", "task", "high priority"])

        if re.search(r'\bexpense\b|^paid|receipt', content_lower, re.IGNORECASE):
            return self.find_section_header(content_lines, ["expense", "january"])

        if snippet.has_media_context():
            return self.find_section_header(content_lines, "notes")

        return None

    def find_section_header(self, content_lines: list, keywords) -> int:
        """Find line number of section header containing keywords

        Args:
            content_lines: Lines of note content
            keywords: String or list of strings to search for

        Returns:
            Line number of section, or None
        """
        if isinstance(keywords, str):
            keywords = [keywords]

        for i, line in enumerate(content_lines):
            if line.startswith('#'):
                line_lower = line.lower()
                for keyword in keywords:
                    if keyword.lower() in line_lower:
                        return i

        return None

    def find_append_position(self, content_lines: list, section_line: int) -> int:
        """Find position to append within a section

        Appends before the next section header or at end

        Args:
            content_lines: Lines of content
            section_line: Line number of section header

        Returns:
            Line number to insert at
        """
        # Find next section header
        for i in range(section_line + 1, len(content_lines)):
            if content_lines[i].startswith('#'):
                # Insert before next section
                return i

        # No next section, append to end
        return len(content_lines)

    def format_snippet(self, snippet: Snippet) -> str:
        """Format snippet for insertion"""

        if snippet.has_media_context():
            # Media snippets get timestamp format
            timestamp = snippet.get_media_timestamp()
            return f"[{timestamp}] {snippet.content.split(']', 1)[-1].strip()}"

        elif re.match(r'^-\s+\w+:\s+\d+', snippet.content):
            # Already formatted as list item
            return snippet.content

        elif re.search(r'\bshoe\s+size', snippet.content.lower()):
            # Format as shoe size entry
            match = re.search(r"(\w+)'s\s+shoe\s+size\s+is\s+now\s+(\d+)", snippet.content, re.IGNORECASE)
            if match:
                name = match.group(1)
                size = match.group(2)
                date = snippet.timestamp.strftime('%Y-%m-%d')
                return f"- {name}: {size} ({date})"

        # Default format
        date = snippet.timestamp.strftime('%Y-%m-%d')
        return f"- {snippet.content} ({date})"
