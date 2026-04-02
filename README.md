# Merger CLI

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/merger-plugin-api.svg?color=orange)](https://pypi.org/project/merger-plugin-api/)

Merger is a **command-line utility** for developers that **scans a directory**, **filters files** using customizable ignore patterns, and **merges all readable content** into a **single output file**, suitable both for **human reading** and for **use by AI models**.

It supports **multiple output formats** (e.g., JSON, directory tree, plain text with file delimiters), and can be extended with **custom file parsers** (e.g., `.pdf`) and **custom exporters** (e.g., `.xml`, `.md`).

This repository is a monorepo containing:
- **`merger-cli`**: The main command-line tool.
- **`merger-plugin-api`**: A lightweight library for building custom plugins.

---

## Quick Start (CLI)

1.  **Install the CLI**: Download the standalone installer for your OS from [Releases](https://github.com/diogotoporcov/merger-cli/releases).
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

## Plugin Development (API)

If you want to extend Merger with custom parsers or exporters, use the `merger-plugin-api`.

1. **Install the API**:
   ```bash
   pip install merger-plugin-api
   ```

2. **Create a Parser**:
   ```python
   from pathlib import Path
   from typing import Union, Type
   from merger_plugin_api import Parser

   class MyParser(Parser):
       @classmethod
       def validate(cls, file_chunk_bytes: Union[bytes, bytearray], file_path: Path) -> bool:
           return file_path.suffix == ".custom"

       @classmethod
       def parse(cls, file_bytes: Union[bytes, bytearray], file_path: Path) -> str:
           return file_bytes.decode("utf-8").upper()

   parser_cls: Type[Parser] = MyParser
   ```

3. **Install your plugin**:
   ```bash
   merger --install-plugin my_parser.py
   ```

For detailed documentation, see the [Merger Plugin API README](packages/merger-plugin-api/README.md).

---

## Features

* **Recursive merge** of all readable files under a root directory.
* **Custom glob-like ignore patterns** with specialized type qualifiers.
* **Intelligent plugin system**: SQLite-backed tracking with automatic dependency management via `uv`.
* **Automatic file encoding detection**.
* **Multiple export formats**: Built-in support for Plain Text, JSON, Directory Trees, and more.
* **Professional CLI**: Modern interface with update notifications and non-interactive mode.

---

## Installation

### Standalone Installation (Recommended)

Merger CLI is distributed as standalone binaries. These include their own Python 3.11 environment and `uv` package manager, requiring **no local Python installation**.

*   **Windows**: Download and run `merger-cli-windows-installer.exe`.
*   **Linux (.deb)**:
    ```bash
    sudo apt install ./merger-cli.deb
    ```
*   **macOS (Homebrew)**:
    ```bash
    brew tap diogotoporcov/merger-cli
    brew install merger-cli
    ```

### From Source

For developers:
1. Clone the repository.
2. Install the API: `pip install -e ./packages/merger-plugin-api`
3. Install the CLI: `pip install -e ./packages/merger-cli`

---

## Plugin System

Merger CLI features a professional plugin architecture. Plugins are standalone Python files that can define their own dependencies via a `REQUIREMENTS` list.

### Managing Plugins
*   **Install**: `merger --install-plugin path/to/plugin.py`
*   **List**: `merger --list-plugins`
*   **Update**: `merger --update-plugins` (Updates dependencies for all installed plugins)
*   **Uninstall**: `merger --uninstall-plugin <plugin_id>` (Automatically purges unused dependencies)

For developers looking to build plugins, see the [Merger Plugin API Documentation](packages/merger-plugin-api/README.md).

---

## Usage Guide

### Output Formats (`-e` / `--exporter`)

| Exporter Name     | File Extension | Description                                                                                    |
|-------------------|----------------|------------------------------------------------------------------------------------------------|
| `TREE_PLAIN_TEXT` | `.txt`         | Directory tree + plain-text merged file contents (**default**).                                |
| `PLAIN_TEXT`      | `.txt`         | Plain-text merged contents with file delimiters.                                               |
| `TREE`            | `.txt`         | Directory tree only.                                                                           |
| `JSON`            | `.json`        | JSON mapping file paths to parsed contents.                                                    |
| `JSON_TREE`       | `.json`        | Structured JSON with hierarchy and metadata.                                                   |

### Ignore Pattern Syntax

Patterns are relative to the scan root. Merger uses **Git-style matching** with custom type qualifiers:

*   `*` matches any number of characters within a path segment.
*   `**` matches zero or more directories.
*   Trailing `/` matches only **directories**.
*   Trailing `:` matches only **files**.
*   Trailing `!` disables type qualification (treats trailing `/` or `:` as literal).

#### Examples
* `*.log`: Ignore all `.log` files recursively.
* `dist/`: Ignore the `dist` directory at the root.
* `src/*.py:`: Ignore all `.py` files directly under the `src` directory.

---

## CLI Options

| Option                     | Description                                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------|
| `INPUT_DIR_PATH`           | Root directory to scan.                                                                     |
| `OUTPUT_FILE_DIR_PATH`     | Directory to save the output (default: `.`).                                                |
| `-e, --exporter`           | Choose the exporter strategy.                                                               |
| `-i, --install-plugin`     | Install a custom parser or exporter plugin.                                                 |
| `-u, --uninstall-plugin`   | Uninstall a plugin by ID (use `*` for all).                                                 |
| `-l, --list-plugins`       | List all installed custom plugins.                                                          |
| `--update-plugins`         | Update dependencies for all installed plugins.                          |
| `--update`                 | Check for CLI updates and provide download links.                                           |
| `--ignore`                 | Glob-style patterns to ignore.                                                              |
| `--merger-ignore`          | Path to ignore file (default: `./merger.ignore`).                                           |
| `-c, --create-ignore`      | Create an ignore file from template (e.g., `PYTHON`, `RUST`).                               |
| `-y, --yes`                | Enable non-interactive mode (auto-confirm prompts).                                         |

---

## License

This project is licensed under the GPLv3 License — see [LICENSE](LICENSE) for details.
