# Merger API

Interfaces and data models for extending the `merger-cli` tool.

This package provides:
- Abstract base classes for custom **Parsers** and **Exporters**.
- Data models for the **File Tree** structure.
- Type definitions for seamless integration with `merger-cli`.

## Installation

```bash
pip install merger-cli-api
```

## Core Interfaces

### Custom Parsers

To support non-text file formats (e.g., PDF, Images), you must implement a custom parser by inheriting from the `Parser` class.

```python
from pathlib import Path
from typing import Union, Optional, Set, Type
from merger_api import Parser

# The list of file extensions this parser supports (e.g., {".pdf"})
EXTENSIONS: Set[str] = {".mock"}

class MockParser(Parser):
    # Optional: Max number of bytes required to validate a file (default: 1024)
    MAX_BYTES_FOR_VALIDATION: Optional[int] = 1024

    @classmethod
    def validate(cls, file_chunk_bytes: Union[bytes, bytearray], file_path: Path) -> bool:
        """
        Validate that the given file represents a supported format.
        Args:
            file_chunk_bytes: The first MAX_BYTES_FOR_VALIDATION bytes of the file.
            file_path: The full path to the file.
        Returns:
            bool: True if this parser can handle the file.
        """
        return True

    @classmethod
    def parse(cls, file_bytes: Union[bytes, bytearray], file_path: Path) -> str:
        """
        Extract text from the file.
        Args:
            file_bytes: The full binary content of the file.
            file_path: The full path to the file.
        Returns:
            str: The extracted text content.
        """
        return "extracted content"

# Your module MUST export this object for merger-cli to load it
parser_cls: Type[Parser] = MockParser
```

### Custom Exporters

To output the merged data in a custom format (e.g., XML, Markdown), implement a `TreeExporter`.

```python
from typing import Type
from merger_api import TreeExporter, FileTree

# The name of the exporter (used in --exporter argument)
NAME = "MY_EXPORTER"
# The extension of the output file
FILE_EXTENSION = ".txt"

class MyExporter(TreeExporter):
    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        """
        Transform the FileTree into bytes (e.g., UTF-8 encoded text).
        """
        return b"exported data"

# Your module MUST export this object for merger-cli to load it
exporter_cls: Type[TreeExporter] = MyExporter
```

## Data Models

The `FileTree` object passed to exporters represents the hierarchical structure of the scanned directory.

### `FileTree`
- `root`: A `DirectoryEntry` representing the scan root.

### `DirectoryEntry`
- `name`: Name of the directory.
- `path`: `pathlib.Path` relative to the scan root.
- `children`: A dictionary mapping names to `FileTreeEntry` (either `FileEntry` or `DirectoryEntry`).

### `FileEntry`
- `name`: Name of the file.
- `path`: `pathlib.Path` relative to the scan root.
- `content`: The parsed text content of the file.
- `extension`: File extension (including the dot).

## Integration

Once you have implemented your custom module, you can install it into `merger-cli`:

```bash
merger --install path/to/your_module.py
```

And then use it:

```bash
merger ./project --exporter MY_EXPORTER
```

For more information, visit the [main repository](https://github.com/diogotoporcov/merger-cli).
