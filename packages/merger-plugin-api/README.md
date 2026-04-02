# Merger Plugin API

[![Python](https://img.shields.io/badge/python-3.8--3.11-blue.svg)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/merger-plugin-api.svg?color=orange)](https://pypi.org/project/merger-plugin-api/)

Interfaces and data models for extending the `merger-cli` tool with custom parsers and exporters.

This package provides:
- Abstract base classes for custom **Parsers** and **Exporters**.
- Data models for the **File Tree** structure.
- Type definitions for seamless integration with `merger-cli`.

---

## Compatibility

The `merger-plugin-api` is designed to be highly compatible to allow plugin developers to use a variety of environments.

- **Supported Python Versions**: 3.8, 3.9, 3.10, and 3.11.

---

## Installation

```bash
pip install merger-plugin-api
```

---

## Creating Plugins

Plugins are standalone Python modules that define a `Parser` or `TreeExporter` class.

### Custom Parsers

To support non-text file formats (e.g., PDF, Images), implement a custom parser. More complete examples like this one are available in the `examples/parsers/` directory.

Here is an example of a PDF parser using `pymupdf`:

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
    MAX_BYTES_FOR_VALIDATION: Optional[int] = None

    @classmethod
    def validate(
        cls,
        file_chunk_bytes: Union[bytes, bytearray],
        file_path: Path
    ) -> bool:
        """
        Validate that the given file bytes represent a readable PDF document.
        """
        try:
            with pymupdf.open(stream=file_chunk_bytes) as doc:
                _ = doc[0]
            return True

        except Exception:
            return False

    @classmethod
    def parse(
        cls,
        file_bytes: Union[bytes, bytearray],
        file_path: Path,
    ) -> str:
        """
        Extracts and concatenates text from all pages of a PDF file.
        """
        texts = []
        with pymupdf.open(stream=file_bytes) as doc:
            for page in doc:
                text = page.get_text()
                if text:
                    text = text.replace("\n\n", "")
                    texts.append(text)

        full_text = " ".join(texts)
        return full_text


# Export the parser class
parser_cls: Type[Parser] = PdfParser
```

### Custom Exporters

To output the merged data in a custom format (e.g., XML, Markdown), implement a `TreeExporter`. More complete examples like this one are available in the `examples/exporters/` directory.

Here is an example of an XML exporter:

```python
import xml.etree.ElementTree as ET
from typing import Type
from merger_plugin_api import FileEntry, DirectoryEntry, FileTreeEntry, TreeExporter, FileTree

# The name of the exporter (used in --exporter argument)
NAME = "XML"
# The extension of the output file
FILE_EXTENSION = ".xml"

class XmlExporter(TreeExporter):
    """
    A custom exporter that generates an XML representation of the file tree.
    """

    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        """
        Export the file tree into an XML representation.
        """
        root = ET.Element("filetree")
        cls._to_xml(tree.root, root)

        cls._indent(root)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    @classmethod
    def _to_xml(cls, entry: FileTreeEntry, parent: ET.Element):
        if isinstance(entry, FileEntry):
            file_el = ET.SubElement(parent, "file", {
                "name": entry.name,
                "path": entry.path.as_posix()
            })
            content_el = ET.SubElement(file_el, "content")
            content_el.text = entry.content

        elif isinstance(entry, DirectoryEntry):
            dir_el = ET.SubElement(parent, "directory", {
                "name": entry.name,
                "path": entry.path.as_posix()
            })
            for child in sorted(entry.children.values(), key=lambda e: e.name.lower()):
                cls._to_xml(child, dir_el)

    @classmethod
    def _indent(cls, elem: ET.Element, level: int = 0):
        """
        Recursive function to indent XML elements while preserving text content.
        """
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "

            if not elem.tail or not elem.tail.strip():
                elem.tail = i

            for child in elem:
                cls._indent(child, level + 1)

            if len(elem) > 0:
                last_child = elem[-1]
                if not last_child.tail or not last_child.tail.strip():
                    last_child.tail = i

        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

# Export the exporter class
exporter_cls: Type[TreeExporter] = XmlExporter
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
