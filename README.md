# Merger CLI

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/merger-cli.svg?color=orange)](https://pypi.org/project/merger-cli/)

Merger is a **command-line utility** for developers that **scans a directory**, **filters files** using customizable ignore patterns, and **merges all readable content** into a **single output file**, suitable both for **human reading** and for **use by AI models**.
It supports **multiple output formats** (e.g., JSON, directory tree, plain text with file delimiters), and can be extended with **custom file parsers** (e.g., `.pdf`) and **custom exporters** (e.g., `.xml`, `.md`).

---

## TLDR

1.  **Install Python 3.8 or newer**
2.  **Install libmagic** if not installed:
    *   **Windows**: Automatically downloaded
    *   **Linux**: `sudo apt-get update && sudo apt-get install libmagic1`  
    *   **macOS**: `brew install libmagic`
3.  **Install the package**: `pip install merger-cli`
4.  **Navigate to your project folder**: `cd path/to/your/project`
5.  **Create a merger ignore file**: Manually or with `merger -c [TEMPLATE]` (Where the template is optional)
6.  **Execute merger-cli**: `merger .` to create a single combined file called `merger.txt`

For more options, refer to the [Usage](#usage) section below.

---

## Summary

1. [Features](#features)
2. [Dependencies](#dependencies)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Ignore Pattern Syntax](#ignore-pattern-syntax)
6. [Output Formats](#output-formats)
7. [Custom Parsers](#custom-parsers)
8. [Custom Exporters](#custom-exporters)
9. [CLI Options](#cli-options)
10. [License](#license)

---

## Features

* **Recursive merge** of all readable files under a root directory.
* **Custom glob-like ignore patterns** for filtering.
* **Automatic file encoding detection**.
* **Modular parser & exporter system** for custom formats and outputs with easy CLI management.
* **Multiple export formats** (built-in and custom).
* **Modern CLI interface**.

---

## Dependencies

* **Python** (3.8+)
* **libmagic**
    *   **Windows**: Automatically downloaded
    *   **Linux**: `sudo apt-get update && sudo apt-get install libmagic1`  
    *   **macOS**: `brew install libmagic`

All Python package requirements are listed in [`requirements.txt`](requirements.txt).

---

## Installation

```bash
pip install merger-cli
```

---

## Usage

### Basic merge

```bash
merger .
```

> **Note:** A `merger.ignore` file is **required** in the current directory for the tool to run. You can create one quickly using `merger --create-ignore`.

This writes a file named `merger.txt` in the current directory.

---

### Save output to a specific directory

```bash
merger ./project ./out
```

This writes `./out/merger.txt` (or `./out/merger.json`, depending on the exporter).

---

### Pick an output format

Use `-e` or `--exporter` to select the output format:

```bash
merger ./src --exporter JSON
```

```bash
merger ./src --exporter DIRECTORY_TREE
```

```bash
merger ./src --exporter PLAIN_TEXT
```

```bash
merger ./src --exporter TREE_PLAIN_TEXT
```

---

### Custom ignore patterns

Provide one or more ignore patterns with `--ignore` (see [Ignore Pattern Syntax](#ignore-pattern-syntax)):

```bash
merger ./project --ignore "*.log" "__pycache__/**" "*.tmp"
```

---

### Custom ignore file

Provide a file containing ignore patterns (one per line) with `--merger-ignore` (see [Ignore Pattern Syntax](#ignore-pattern-syntax)):

```bash
merger . --merger-ignore "C:\Users\USER\Desktop\ignore.txt"
```

---

### Custom ignore templates

Quickly create a `merger.ignore` file using built-in templates:

```bash
merger -c PYTHON
```

Supported templates: `DEFAULT`, `PYTHON`, `JAVASCRIPT`, `TYPESCRIPT`, `JAVA`, `GO`, `RUST`, `CPP`, `CSHARP`, `RUBY`, `PHP`, `KOTLIN`.

---

### Custom modules (Parsers & Exporters)

List all installed custom modules (parsers and exporters):

```bash
merger --list
```

---

### Verbose output

```bash
merger ./src --log-level DEBUG
```

---

## Ignore Pattern Syntax

Ignore patterns are evaluated **relative to the input directory** (the scan root). `merger-cli` uses standard **Git-style matching** (via `pathspec`), with some additional custom qualifiers.

### Recursive vs. Anchored

*   **Recursive**: Patterns with **no slashes** (or starting with `**/`) match anywhere in the directory tree.
    *   Example: `*.log` matches `root/app.log` and `root/logs/app.log`.
*   **Anchored**: Patterns with **at least one internal slash** or a **leading slash** are anchored to the scan root.
    *   Example: `src/*.py` matches `root/src/main.py` but **not** `root/project/src/main.py`.
    *   Example: `/config.json` matches `root/config.json` but **not** `root/subdir/config.json`.
*   **Leading `./`**: Normalized to `/` and treated as an anchored pattern.

### Pattern Components

*   `*` matches any number of characters within a single path segment.
*   `**` matches zero or more directories.
    *   Example: `**/node_modules/` matches `node_modules` at any depth.
*   `?` matches exactly one character.
*   `[seq]` matches any character in *seq*.

### Type qualifiers

* Trailing `/` requires the matched path to be a **directory**
  * Example: `build/` matches the `build` directory entry


* Trailing `:` requires the matched path to be a **file**
  * Example: `README.md:` matches the `README.md` file


* Trailing `!`:
  * This is a special escape suffix that disables type qualification and preserves
    any trailing `/` or `:` as literal characters in the final path segment

    * Examples:
      * `data:!` matches any file or directory literally named `data:`
      * `data::` matches any file literally named `data:`
      * `data:/` matches any directory literally named `data:`
      * `data!!` matches any file or directory literally named `data!`
      * `data!/` matches any directory literally named `data!`
      * `data!:` matches any file literally named `data!`


### Examples

Ignore all files or directories that end with `.log`:
* `*.log` (Recursive)

Ignore the `dist` directory at the scan root:
* `dist/` (Anchored because it has a slash)

Ignore all `node_modules` directories anywhere:
* `**/node_modules/` (Recursive)

Ignore a file named `config.json` at the scan root:
* `/config.json:`

Ignore all `.py` files directly under the **root** `src` directory:
* `src/*.py:`

Ignore all `__pycache__` directories inside the **root** `src` directory:
* `src/**/__pycache__/`

Ignore all files `data:`:
* `data::`

Ignore all directories `data:`:
* `data:/`

Ignore all files or directories `data:`:
* `data:!`

---

## Output Formats

Merger writes **one output file** to the output directory, named `merger.<extension>` based on the selected exporter.

| Exporter Name     | File Extension | Description                                                                                    |
|-------------------|----------------|------------------------------------------------------------------------------------------------|
| `TREE_PLAIN_TEXT` | `.txt`         | Directory tree + plain-text merged file contents (**default**).                                |
| `PLAIN_TEXT`      | `.txt`         | Plain-text merged file contents with `<<FILE_START>>` / `<<FILE_END>>` file delimiter.         |
| `TREE`            | `.txt`         | Directory tree only.                                                                           |
| `JSON`            | `.json`        | JSON mapping file paths to parsed file contents (`path: content`).                             |
| `JSON_TREE`       | `.json`        | Structured JSON representing the directory tree and file contents with hierarchy and metadata. |

---

## Custom Parsers

Merger uses **parser strategies** to support parsing of non-text file formats (e.g., PDF, images with OCR, etc.).

---

### Parser Abstract Class

All parsers must inherit from `Parser`:

```python
from merger.parsing.parser import Parser
```

Required structure:

*   `EXTENSIONS: Set[str]` (e.g., `{".pdf"}`)
*   `MAX_BYTES_FOR_VALIDATION: Optional[int]`
*   `validate(cls, file_chunk_bytes, *, file_path=None, logger=None) -> bool`
*   `parse(cls, file_bytes, *, file_path=None, logger=None) -> str`

---

### Managing Custom Parsers

To install a module:

```bash
merger --install path/to/parser.py
```

To uninstall a module (`*` removes all modules including parsers and exporters):

```bash
merger --uninstall <module_id>
```

To list installed modules:

```bash
merger --list
```

---

### Custom Parser Example (PDF)

```python
import logging
from pathlib import Path
from typing import Union, Optional, Set, Type

import pymupdf
from merger.parsing.parser import Parser


class PdfParser(Parser):
    EXTENSIONS: Set[str] = {".pdf"}
    MAX_BYTES_FOR_VALIDATION: Optional[int] = None

    @classmethod
    def validate(
        cls,
        file_chunk_bytes: Union[bytes, bytearray],
        *,
        file_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ) -> bool:
        """
        Validate that the given file represents a readable PDF document.

        Args:
            file_chunk_bytes: Binary contents of the file being validated, sufficient to perform validation.
            file_path: Path of the file being validated.
            logger: Optional logger instance for logging.

        Returns:
            bool: True if the file is a readable PDF, False otherwise.
        """
        try:
            with pymupdf.open(file_path) as doc:
                _ = doc[0]
            return True

        except Exception:
            return False

    @classmethod
    def parse(
        cls,
        file_bytes: Union[bytes, bytearray],
        *,
        file_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ) -> str:
        """
        Extracts and concatenates text from all pages of a PDF file.

        Args:
            file_bytes: Binary contents of the file being parsed.
            file_path: Path of the file being parsed.
            logger: optional logger instance for logging.

        Returns:

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


parser_cls: Type[Parser] = PdfParser
```

Available at [`examples/custom_parsers/pdf_parser.py`](examples/custom_parsers/pdf_parser.py).

> The module **must expose a `parser_cls` object** referencing the parser class.

---

## Custom Exporters

You can also extend Merger with **custom export strategies** to output data in any format (e.g., XML, Markdown, CSV).

---

### Exporter Abstract Class

All exporters must inherit from `TreeExporter`:

```python
from merger.exporters.tree_exporter import TreeExporter
```

Required structure:

*   `NAME: str` (The name used in `--exporter`)
*   `FILE_EXTENSION: str` (The output file extension)
*   `export(cls, tree: FileTree) -> bytes`

---

### Managing Custom Exporters

To install an exporter:

```bash
merger --install path/to/exporter.py
```

To uninstall an exporter (`*` removes all modules including parsers and exporters):

```bash
merger --uninstall <exporter_id>
```

To list installed exporters:

```bash
merger --list
```

---

### Custom Exporter Example (XML)

```python
import xml.etree.ElementTree as ET

from merger.file_tree.entries import FileEntry, DirectoryEntry, FileTreeEntry
from merger.exporters.tree_exporter import TreeExporter
from merger.file_tree.tree import FileTree


class XmlExporter(TreeExporter):
    """
    A custom exporter that generates an XML representation of the file tree.
    """
    NAME = "XML"
    FILE_EXTENSION = ".xml"

    @classmethod
    def export(cls, tree: FileTree) -> bytes:
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

exporter_cls = XmlExporter
```

Available at [`examples/custom_exporters/xml_exporter.py`](examples/custom_exporters/xml_exporter.py).

> The module **must expose an `exporter_cls` object** referencing the exporter class.

---

## CLI Options

| Option                     | Description                                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------|
| `input_dir`                | Root directory to scan for files.                                                           |
| `output_path`              | Output directory where the tool writes `merger.<ext>` (default: current directory).         |
| `-e, --exporter`           | Output exporter strategy (e.g., `TREE_PLAIN_TEXT`, `PLAIN_TEXT`, `JSON`, `XML`).            |
| `-i, --install`            | Install a custom module (parser or exporter).                                               |
| `-u, --uninstall`          | Uninstall a module by ID (`*` removes all modules including parsers and exporters).         |
| `-l, --list`               | List all installed custom modules.                                                          |
| `--ignore`                 | One or more ignore patterns (see [Ignore Pattern Syntax](#ignore-pattern-syntax)).          |
| `--merger-ignore`          | File containing ignore patterns (default: `./merger.ignore`).                               |
| `-c, --create-ignore`      | Create a `merger.ignore` file using a built-in template (e.g., `DEFAULT`, `PYTHON`).        |
| `--version`                | Show installed version.                                                                     |
| `--log-level`              | Set logging verbosity.                                                                      |

---

## License

This project is licensed under the GPLv3 License — see [LICENSE](LICENSE) for details.