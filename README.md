# Merger CLI

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/merger-cli.svg?color=orange)](https://pypi.org/project/merger-cli/)

Merger is a **command-line utility** for developers that **scans a directory**, **filters files** using customizable ignore patterns, and **merges all readable content** into a **single structured output file**, suitable both for **human reading** and for **use by AI models**.

It supports **multiple output formats** (e.g., JSON, directory tree, plain text with file delimiters), and can be extended with **custom file parsers** (e.g., `.pdf`) and **custom exporters** (e.g., `.xml`, `.md`).

---

## Quick Start

1.  **Install the CLI**:
    ```bash
    pip install merger-cli
    ```
    *(For global installation, it is recommended to use `pipx install merger-cli`)*

2.  **Verify the installation**:
    ```bash
    merger --version
    ```

3.  **Navigate to your project**:
    ```bash
    cd path/to/your/project
    ```

4.  **Create an ignore file**:
    ```bash
    merger -c PYTHON
    ```

5.  **Run Merger**:
    ```bash
    merger .
    ```
    This creates `merger.txt` in the current directory.

---

## Features

* **Recursive merge** of all readable files under a root directory.
* **Custom glob-like ignore patterns** with specialized type qualifiers for precise filtering.
* **Intelligent plugin system**: Built on Abstract Base Classes (ABCs) for easy extensibility with custom parsers and exporters.
* **Automatic file encoding detection** for seamless merging of various text files.
* **Multiple export formats**: Built-in support for Plain Text, JSON, Directory Trees, and structured combinations.
* **Modern CLI interface**: Rich-powered output, update notifications, and non-interactive mode.

---

## Installation

Merger requires **Python 3.8+** and **libmagic**.

### Using pipx (Recommended for Global Use)

```bash
pipx install merger-cli
```

### Using pip

```bash
pip install merger-cli
```

### From Source

```bash
git clone https://github.com/diogotoporcov/merger-cli.git
cd merger-cli
pip install .
```

### System Dependencies (libmagic)

Merger uses `libmagic` to detect file types.
*   **Windows**: Automatically handled by `python-magic-bin`.
*   **Linux**: `sudo apt-get update && sudo apt-get install libmagic1`
*   **macOS**: `brew install libmagic`

---

## Usage Guide

### Basic Merge
```bash
merger .
```
This scans the current directory and writes a combined file named `merger.txt`. 
> **Note:** A `merger.ignore` file is required. You can create one using the `--create-ignore` option.

### Output Path
```bash
merger ./project ./out
```
This will save the output file to the specified directory (e.g., `./out/merger.txt`).

### Selecting an Exporter
Use `-e` or `--exporter` to choose the output format:
```bash
merger . --exporter JSON
```

### Custom Ignore Patterns
You can provide additional patterns directly via the CLI:
```bash
merger . --ignore "*.log" "temp/**"
```

### Custom Ignore Templates
Quickly generate a `merger.ignore` file from built-in templates:
```bash
merger -c PYTHON
```
Supported templates include: `DEFAULT`, `PYTHON`, `JAVASCRIPT`, `RUST`, `GO`, `CPP`, and many more.

---

## Ignore Pattern Syntax

Merger uses **Git-style matching** with custom type qualifiers. Patterns are evaluated relative to the scan root.

### Special Qualifiers
*   Trailing `/` matches only **directories**.
*   Trailing `:` matches only **files**.
*   Trailing `!` disables type qualification (treats trailing `/` or `:` as literal characters).
*   Leading `!` negates the pattern (do **not** ignore).

### Examples

| Pattern           | Type          | Effect                                                                                                |
|:------------------|:--------------|:------------------------------------------------------------------------------------------------------|
| `node_modules/`   | **Directory** | Ignores the `node_modules` directory and all its contents.                                            |
| `config.json:`    | **File**      | Ignores only files named `config.json`.                                                               |
| `temp/`           | **Directory** | Ignores any directory named `temp` anywhere in the tree.                                              |
| `build!/`         | **Literal**   | Ignores a file or directory named `build/` literally.                                                 |
| `src/*.py:`       | **File**      | Ignores all `.py` files directly under the `src` directory.                                           |
| `!important.log:` | **Negation**  | Explicitly includes `important.log` even if other patterns match it.                                  |

---

## Output Formats

| Exporter Name     | File Extension | Description                                                                                    |
|-------------------|----------------|------------------------------------------------------------------------------------------------|
| `TREE_TEXT`       | `.txt`         | Directory tree followed by plain-text merged file contents (**default**).                      |
| `TEXT`            | `.txt`         | Plain-text merged contents with clear file delimiters.                                         |
| `TREE`            | `.txt`         | Directory tree structure only.                                                                 |
| `JSON`            | `.json`        | Flat JSON mapping file paths to their parsed contents.                                         |
| `JSON_TREE`       | `.json`        | Structured JSON representing the directory hierarchy with metadata and contents.               |

---

## Plugins (Parsers & Exporters)

Merger features a flexible plugin architecture. Plugins are standalone Python files that extend the tool's capabilities.

### Custom Parsers

To support non-text files (e.g., PDF, images), create a parser that inherits from `merger.parsing.base.Parser`.

```python
from pathlib import Path
from typing import Union, Set, Type, Optional
import pymupdf
from merger.parsing.base import Parser

class PdfParser(Parser):
    # Optional: bytes to read for validation (default: 1024)
    MAX_BYTES_FOR_VALIDATION: Optional[int] = None

    @classmethod
    def validate(cls, file_chunk_bytes: Union[bytes, bytearray], file_path: Path) -> bool:
        # Check if the file starts with PDF signature or is readable as PDF
        return file_path.suffix.lower() == ".pdf"

    @classmethod
    def parse(cls, file_bytes: Union[bytes, bytearray], file_path: Path) -> str:
        # Extract text from PDF
        texts = []
        with pymupdf.open(stream=file_bytes) as doc:
            for page in doc:
                texts.append(page.get_text())
        return "\n".join(texts)

# Required module-level variables
EXTENSIONS: Set[str] = {".pdf"}
parser_cls: Type[Parser] = PdfParser
```

### Custom Exporters

To output data in a new format (e.g., XML, Markdown), create an exporter that inherits from `merger.exporters.base.TreeExporter`.

```python
from typing import Type
from merger.exporters.base import TreeExporter
from merger.models import FileTree, FileEntry, DirectoryEntry

class MarkdownExporter(TreeExporter):
    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        lines = ["# Project File Tree", ""]
        cls._build_md(tree.root, lines)
        return "\n".join(lines).encode("utf-8")

    @classmethod
    def _build_md(cls, entry, lines, level=2):
        if isinstance(entry, FileEntry):
            lines.append(f"{'#' * level} File: `{entry.name}`")
            lines.append(f"```\n{entry.content}\n```\n")
        elif isinstance(entry, DirectoryEntry):
            lines.append(f"{'#' * level} Directory: `{entry.name}`")
            for child in entry.children.values():
                cls._build_md(child, lines, level + 1)

# Required module-level variables
NAME = "MARKDOWN"
FILE_EXTENSION = ".md"
exporter_cls: Type[TreeExporter] = MarkdownExporter
```

### Managing Plugins

```bash
# Install a custom parser or exporter
merger --install-plugin path/to/plugin.py

# List all installed custom plugins
merger --list-plugins

# Uninstall a plugin by its ID
merger --uninstall-plugin <plugin_id>
```

---

## CLI Options

| Option                   | Description                                                    |
|--------------------------|----------------------------------------------------------------|
| `INPUT_DIR_PATH`         | Root directory to scan for files.                              |
| `OUTPUT_FILE_DIR_PATH`   | Directory to save the output (default: `.`).                   |
| `-e, --exporter`         | Choose the exporter strategy.                                  |
| `-i, --install-plugin`   | Install a custom parser or exporter plugin.                    |
| `-u, --uninstall-plugin` | Uninstall a plugin by ID (`*` for all).                        |
| `-l, --list-plugins`     | List all installed custom plugins.                             |
| `-c, --create-ignore`    | Create an ignore file from template (e.g., `PYTHON`).          |
| `--ignore`               | One or more glob-style patterns to ignore.                     |
| `--merger-ignore`        | Path to ignore file (default: `./merger.ignore`).              |
| `-y, --yes`              | Non-interactive mode (auto-confirm prompts).                   |
| `--version`              | Show program version and exit.                                 |
| `--log-level`            | Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).     |

---

## License

This project is licensed under the GPLv3 License — see [LICENSE](LICENSE) for details.
