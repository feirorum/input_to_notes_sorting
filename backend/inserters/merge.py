from .base import BaseInserter
from models.note import Note
from models.snippet import Snippet
from typing import Tuple


class MergeInserter(BaseInserter):
    """Merges snippet into existing note content"""

    def insert(self, snippet: Snippet, note: Note) -> Tuple[str, dict]:
        """Merge snippet into note

        For demo purposes, this adds to a relevant section or creates
        a new "Recent Updates" section
        """

        # Create undo info
        undo_info = {
            "original_content": note.content,
            "note_id": note.id,
            "operation": "merge",
            "snippet_content": snippet.content
        }

        # For now, implement as append to a "Recent Updates" section
        # In a more sophisticated version, this would intelligently
        # merge into existing paragraphs

        content_lines = note.content.split('\n')

        # Look for "Recent Updates" section
        recent_updates_line = None
        for i, line in enumerate(content_lines):
            if "recent update" in line.lower() and line.startswith('#'):
                recent_updates_line = i
                break

        date_str = snippet.timestamp.strftime('%Y-%m-%d')

        if recent_updates_line is not None:
            # Find insertion point (after section header, before next section)
            insert_pos = recent_updates_line + 1

            # Skip existing content
            while insert_pos < len(content_lines):
                if content_lines[insert_pos].startswith('#'):
                    break
                insert_pos += 1

            # Insert with date
            formatted = f"\n### {date_str}\n{snippet.content}\n"
            content_lines.insert(insert_pos, formatted)
        else:
            # Add new "Recent Updates" section
            content_lines.append("\n## Recent Updates\n")
            content_lines.append(f"### {date_str}\n{snippet.content}\n")

        modified_content = '\n'.join(content_lines)

        return modified_content, undo_info
