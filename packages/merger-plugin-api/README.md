# Merger Plugin API

[![PyPI](https://img.shields.io/pypi/v/merger-plugin-api.svg?color=orange)](https://pypi.org/project/merger-plugin-api/)

Interfaces and data models for extending the `merger-cli` tool with custom parsers and exporters.

This package provides:
- Abstract base classes for custom **Parsers** and **Exporters**.
- Data models for the **File Tree** structure.
- Type definitions for seamless integration with `merger-cli`.

---

## Installation

```bash
pip install merger-plugin-api
```

---

## Creating Plugins

Plugins are standalone Python modules that define a `Parser` or `TreeExporter` class.

### Custom Parsers

To support non-text file formats (e.g., PDF, Images), implement a custom parser. Here is an example of a PDF parser using `pymupdf`:

```python
from pathlib import Path
from typing import Union, Optional, Set, Type
import pymupdf
from merger_plugin_api import Parser

# Optional: List of Python packages required for this plugin
REQUIREMENTS = ["pymupdf"]

# File extensions this parser supports
EXTENSIONS: Set[str] = {".pdf"}

class PdfParser(Parser):
    # Optional: Max number of bytes required to validate a file (default: 1024)
    MAX_BYTES_FOR_VALIDATION: Optional[int] = None

    @classmethod
    def validate(cls, file_chunk_bytes: Union[bytes, bytearray], file_path: Path) -> bool:
        """Validate that the given file bytes represent a readable PDF document."""
        try:
            with pymupdf.open(stream=file_chunk_bytes) as doc:
                _ = doc[0]
            return True
        except Exception:
            return False

    @classmethod
    def parse(cls, file_bytes: Union[bytes, bytearray], file_path: Path) -> str:
        """Extracts and concatenates text from all pages of a PDF file."""
        texts = []
        with pymupdf.open(stream=file_bytes) as doc:
            for page in doc:
                text = page.get_text()
                if text:
                    texts.append(text.replace("\n\n", ""))
        return " ".join(texts)

# Export the parser class
parser_cls: Type[Parser] = PdfParser
```

### Custom Exporters

To output the merged data in a custom format (e.g., XML, Markdown), implement a `TreeExporter`. Here is an example of a Markdown exporter:

```python
from typing import Type, List
from merger_plugin_api import TreeExporter, FileTree, FileEntry, DirectoryEntry

# The name of the exporter (used in --exporter argument)
NAME = "MARKDOWN"
# The extension of the output file
FILE_EXTENSION = ".md"

class MarkdownExporter(TreeExporter):
    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        """Transform the FileTree into a Markdown string."""
        lines = ["# Project File Tree", ""]
        cls._to_markdown(tree.root, lines, level=2)
        return "\n".join(lines).encode("utf-8")

    @classmethod
    def _to_markdown(cls, entry, lines: List[str], level: int):
        if isinstance(entry, FileEntry):
            lines.append(f"{'#' * level} File: `{entry.name}`\nPath: `{entry.path.as_posix()}`\n\n```\n{entry.content}\n```\n")
        elif isinstance(entry, DirectoryEntry):
            lines.append(f"{'#' * level} Directory: `{entry.name}`\nPath: `{entry.path.as_posix()}`\n")
            for child in sorted(entry.children.values(), key=lambda e: e.name.lower()):
                cls._to_markdown(child, lines, level + 1)

# Export the exporter class
exporter_cls: Type[TreeExporter] = MarkdownExporter
```

---

## Data Models

The `FileTree` object represents the hierarchical structure of the scanned directory.

### `FileTree`
- `root`: A `DirectoryEntry` representing the scan root.

### `DirectoryEntry`
- `name`: Name of the directory.
- `path`: `pathlib.Path` relative to the scan root.
- `children`: A dictionary mapping names to `FileTreeEntry` (`FileEntry` or `DirectoryEntry`).

### `FileEntry`
- `name`: Name of the file.
- `path`: `pathlib.Path` relative to the scan root.
- `content`: The parsed text content of the file.
- `extension`: File extension (including the dot).

---

## Using Your Plugins

Once you have implemented your plugin, install it via the CLI:

```bash
merger --install-plugin path/to/your_plugin.py
```

Merger will automatically detect if it's a parser or exporter and install any listed `REQUIREMENTS` using its internal `uv` manager.

For more information, visit the [main repository](https://github.com/diogotoporcov/merger-cli).
