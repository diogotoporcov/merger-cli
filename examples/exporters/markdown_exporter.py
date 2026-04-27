from typing import List

from merger.exporters.base import TreeExporter
from merger.models import FileEntry, DirectoryEntry, FileTreeEntry, FileTree

# The name of the exporter (used in --exporter argument)
NAME = "MARKDOWN"
# The extension of the output file
FILE_EXTENSION = ".md"


class MarkdownExporter(TreeExporter):
    """
    A custom exporter that generates a Markdown representation of the file tree.
    """

    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        """
        Export the file tree into a Markdown representation.
        """
        lines = ["# Project File Tree", ""]
        cls._to_markdown(tree.root, lines, level=2)
        return "\n".join(lines).encode("utf-8")

    @classmethod
    def _to_markdown(cls, entry: FileTreeEntry, lines: List[str], level: int):
        if isinstance(entry, FileEntry):
            lines.append(f"{'#' * level} File: `{entry.name}`")
            lines.append(f"Path: `{entry.path.as_posix()}`")
            lines.append("")
            lines.append("```")
            lines.append(entry.content)
            lines.append("```")
            lines.append("")

        elif isinstance(entry, DirectoryEntry):
            lines.append(f"{'#' * level} Directory: `{entry.name}`")
            lines.append(f"Path: `{entry.path.as_posix()}`")
            lines.append("")
            for child in sorted(entry.children.values(), key=lambda e: e.name.lower()):
                cls._to_markdown(child, lines, level + 1)

# Export the exporter class
exporter_cls = MarkdownExporter
