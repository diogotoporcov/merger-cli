# Merger CLI

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/merger-cli.svg?color=orange)](https://pypi.org/project/merger-cli/)

Merger is a **command-line utility** for developers that **scans a directory**, **filters files** using customizable ignore patterns, and **merges all readable content** into a **single output file**, suitable both for **human reading** and for **use by AI models**.
It supports **multiple output formats** (e.g., JSON, directory tree, plain text with file delimiters), and can be extended with **custom file parsers** (e.g., `.pdf`) and **custom exporters** (e.g., `.xml`, `.md`).

---

## TLDR

1.  **Install**: `pip install merger-cli`
2.  **Setup**: `merger -c` (creates a `merger.ignore` file. **Note**: A `.ignore` file is needed to filter output; if you don't have one, use this command)
3.  **Run**: `merger .` (merges the current directory into `merger.txt`)

---

## Summary

1. [Core Features](#core-features)
2. [Dependencies](#dependencies)
3. [Installation with PyPI](#installation-with-pypi)
4. [Build and Install Locally](#build-and-install-locally)
5. [Usage](#usage)
6. [Testing](#testing)
7. [Ignore Pattern Syntax](#ignore-pattern-syntax)
8. [Output Formats](#output-formats)
9. [Custom Parsers](#custom-parsers)
10. [Custom Exporters](#custom-exporters)
11. [CLI Options](#cli-options)
12. [License](#license)

---

## Core Features

* **Recursive merge** of all readable files under a root directory.
* **Custom glob-like ignore patterns** for filtering.
* **Automatic file encoding detection**.
* **Modular parser & exporter system** for custom formats and outputs with easy CLI management.
* **Multiple export formats** (built-in and custom).
* **Modern CLI interface** with formatted tables and clear logging using `rich`.
* **Automatic configuration migration** and versioning support.

---

## Dependencies

| Component    | Version | Notes    |
|--------------|---------|----------|
| **Python**   | ≥ 3.8   | Required |
| **Pydantic** | ≥ 2.0   | Required |
| **Rich**     | ≥ 13.0  | Required |

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

List all installed custom modules:

```bash
merger --list-modules    # List parsers
merger --list-exporters  # List exporters
```

---

### Verbose output

```bash
merger ./src --log-level DEBUG
```

---

## Testing

Merger uses `pytest` for testing. To run tests locally:

1.  **Install test dependencies**:
    ```bash
    pip install -e ".[test]"
    ```
2.  **Run tests**:
    ```bash
    pytest
    ```

Tests are also automatically run via GitHub Actions on every push and pull request, covering Python versions 3.8 to 3.13.

---

## Ignore Pattern Syntax

Ignore patterns are evaluated **relative to the input directory** (the directory you ask `merger` to scan). If a path is not located under that root, it will not match.

### Segment matching

The pattern is split into segments and matched against the scanned path’s relative segments.

Supported segments:

* Literal segments (e.g. `src`, `tests`, `README.md`)
* `*` matches **exactly one** path segment
* `**` matches **zero or more** path segments
* Embedded `*` inside a segment matches `prefix*suffix` (e.g. `foo*.py`, `*cache*`)

### Anchoring

* Leading `/` anchors the pattern to the scan root
  * Example: `/src/*.py` matches `src/main.py` but not `project/src/main.py`
  

* Leading `./` anchors the pattern to the start of the relative path (equivalent anchoring behavior)
  * Example: `./src/*.py` matches `src/main.py` but not `project/src/main.py`
  

* Without anchoring, the pattern may match starting at **any segment boundary** within the relative path
  * Example: `src/*.py` matches both `src/main.py` and `project/src/main.py`

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

Ignore all files or directorys that contains `.log` prefix:
* `*.log`

Ignore all `dist` directories:
* `dist/`

Ignore a file named `config.json` at the scan root:
* `/config.json:`

Ignore all `.py` file directly under any `src` directory (but not deeper):
* `src/*.py:`

Ignore all file or directories that contains `cache` and is only one level deep inside any directory named `src`:
* `src/*/*cache*`

Ignore all `__pycache__` directories inside the `src` directory at the scan root:
* `./src/**/__pycache__/`

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
merger --install-module path/to/parser.py
```

To uninstall a module:

```bash
merger --uninstall-module <module_id>  # '*' removes all
```

To list installed modules:

```bash
merger --list-modules
```

---

### Custom Parser Example (PDF)

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
merger --install-exporter path/to/exporter.py
```

To uninstall an exporter:

```bash
merger --uninstall-exporter <exporter_id>  # '*' removes all
```

To list installed exporters:

```bash
merger --list-exporters
```

---

### Custom Exporter Example (XML)

```python
from merger.exporters.tree_exporter import TreeExporter

class XmlExporter(TreeExporter):
    NAME = "XML"
    FILE_EXTENSION = ".xml"

    @classmethod
    def export(cls, tree) -> bytes:
        # Implementation logic...
        return b"<root>...</root>"

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
| `-i, --install-module`     | Install a custom parser module.                                                             |
| `-u, --uninstall-module`   | Uninstall a parser module by ID (`*` removes all).                                          |
| `-l, --list-modules`       | List installed parser modules.                                                              |
| `--install-exporter`       | Install a custom exporter module.                                                           |
| `--uninstall-exporter`     | Uninstall an exporter module by ID (`*` removes all).                                       |
| `--list-exporters`         | List installed exporter modules.                                                            |
| `--ignore`                 | One or more ignore patterns (see [Ignore Pattern Syntax](#ignore-pattern-syntax)).          |
| `--merger-ignore`          | File containing ignore patterns (default: `./merger.ignore`).                               |
| `-c, --create-ignore`      | Create a `merger.ignore` file using a built-in template (e.g., `DEFAULT`, `PYTHON`).        |
| `--version`                | Show installed version.                                                                     |
| `--log-level`              | Set logging verbosity.                                                                      |

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.