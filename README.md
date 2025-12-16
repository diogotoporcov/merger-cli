# Merger CLI

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/merger-cli.svg?color=orange)](https://pypi.org/project/merger-cli/)

Merger is a **command-line utility** for developers that **scans a directory**, **filters files** using customizable ignore patterns, and **merges all readable content** into a **single output file**, suitable both for **human reading** and for **use by AI models**.
It supports **multiple output formats** (e.g., JSON, directory tree, plain text with file delimiters), and can be extended with **custom file parsers** for formats, such as `.pdf`.

---

## Summary

1. [Core Features](#core-features)
2. [Dependencies](#dependencies)
3. [Installation with PyPI](#installation-with-pypi)
4. [Build and Install Locally](#build-and-install-locally)
5. [Usage](#usage)
6. [Output Formats](#output-formats)
7. [Custom Parsers](#custom-parsers)
8. [CLI Options](#cli-options)
9. [License](#license)

---

## Core Features

* **Recursive merge** of all readable files under a root directory.
* **Glob-based ignore patterns** using `.gitignore`-style syntax.
* **Automatic file encoding detection**.
* **Modular parser system** for custom formats.
* **CLI support** for installation, removal, and listing of custom parsers.
* **Multiple export formats**.

---

## Dependencies

| Component  | Version | Notes    |
|------------|---------|----------|
| **Python** | ≥ 3.8   | Required |

All dependencies are listed in [`requirements.txt`](requirements.txt).

---

## Installation with PyPI

```bash
pip install merger-cli
```

---

## Build and Install Locally

### 1. Clone the repository

```bash
git clone https://github.com/diogotoporcov/merger-cli.git
cd merger-cli
```

### 2. Create and activate a virtual environment

**Linux / macOS**

```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install as CLI tool

```bash
pip install .
```

---

## Usage

### Basic merge

```bash
merger .
```

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

```bash
merger ./project --ignore "*.log" "__pycache__" "*.tmp"
```

---

### Custom ignore file

```bash
merger . --merger-ignore "C:\Users\USER\Desktop\ignore.txt"
```

---

### Verbose output

```bash
merger ./src --log-level DEBUG
```

---

## Output Formats

Merger writes **one output file** to the output directory, named `merger.<ext>` based on the selected exporter.

| Exporter Name     | File Extension | Description                                                                            |
|-------------------|----------------|----------------------------------------------------------------------------------------|
| `PLAIN_TEXT`      | `.txt`         | Plain-text merged file contents with `<<FILE_START>>` / `<<FILE_END>>` file delimiter. |
| `DIRECTORY_TREE`  | `.txt`         | Directory tree only.                                                                   |
| `TREE_PLAIN_TEXT` | `.txt`         | Directory tree + plain-text merged file contents (**default**).                        |
| `JSON`            | `.json`        | Structured JSON representing the directory tree and file contents.                     |

---

## Custom Parsers

Merger uses **parser strategies** to support parsing of non-text file formats.

---

### Parser Abstract Class

All parsers must inherit from `Parser`:

```python
from merger.parsing.parser import Parser
```

Required structure:

* `EXTENSIONS: Set[str]`
* `MAX_BYTES_FOR_VALIDATION: Optional[int]`
* `validate(cls, file_chunk_bytes, *, file_path=None, logger=None) -> bool`
* `parse(cls, file_bytes, *, file_path=None, logger=None) -> str`

---

### Installing a Custom Parser

```bash
merger --install-module path/to/parser.py
```

To uninstall a module:

```bash
merger --uninstall-module <module_id>
```

To remove all modules:

```bash
merger --uninstall-module *
```

To list installed modules:

```bash
merger --list-modules
```

---

### Custom Parser Implementation Example (PDF)

```python
import logging
from pathlib import Path
from typing import Union, Optional, Any, Set, Type

import fitz

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
            with fitz.open(file_path) as doc:
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
            logger: ptional logger instance for logging.

        Returns:

        """
        texts = []
        with fitz.open(stream=file_bytes) as doc:
            for page in doc:
                text = page.get_text()
                if text:
                    text = text.replace("\n\n", "")
                    texts.append(text)

        full_text = " ".join(texts)
        return full_text


parser_cls: Type[Parser] = PdfParser
```

> The module **must expose a `parser_cls` object** referencing the parser class.

This implementation is available at [`examples/custom_parsers/pdf_parser.py`](examples/custom_parsers/pdf_parser.py).

---

## CLI Options

| Option                   | Description                                                                                 |
|--------------------------|---------------------------------------------------------------------------------------------|
| `input_dir`              | Root directory to scan for files.                                                           |
| `output_path`            | Output directory where the tool writes `merger.<ext>` (default: current directory).         |
| `-e, --exporter`         | Output exporter strategy (e.g., `TREE_PLAIN_TEXT`, `PLAIN_TEXT`, `DIRECTORY_TREE`, `JSON`). |
| `-i, --install-module`   | Install a custom parser module.                                                             |
| `-u, --uninstall-module` | Uninstall a parser module by ID (`*` removes all).                                          |
| `-l, --list-modules`     | List installed parser modules.                                                              |
| `--ignore`               | Glob-style ignore patterns.                                                                 |
| `--merger-ignore`        | File containing glob-style patterns to ignore (default: `./merger.ignore`).                 |
| `--version`              | Show installed version.                                                                     |
| `--log-level`            | Set logging verbosity.                                                                      |

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
