# Merger CLI

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/merger-plugin-api.svg?color=orange)](https://pypi.org/project/merger-plugin-api/)

Merger is a **command-line utility** for developers that **scans a directory**, **filters files** using customizable ignore patterns, and **merges all readable content** into a **single output file**, suitable both for **human reading** and for **use by AI models**.

It supports **multiple output formats** (e.g., JSON, directory tree, plain text with file delimiters), and can be extended with **custom file parsers** (e.g., `.pdf`) and **custom exporters** (e.g., `.xml`, `.md`).

---

## Quick Start

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

## Features

* **Recursive merge** of all readable files under a root directory.
* **Custom glob-like ignore patterns** with specialized type qualifiers.
* **Intelligent plugin system**: SQLite-backed tracking with automatic dependency management via `uv`.
* **Automatic file encoding detection**.
* **Multiple export formats**: Built-in support for Plain Text, JSON, Directory Trees, and more.
* **Modern CLI interface**: Update notifications and non-interactive mode.

---

## Installation

### Standalone Installation (Recommended)

Merger CLI is distributed as standalone binaries.

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

### Detailed Ignore Examples

Merger uses a specialized syntax to distinguish between files and directories, and to handle edge cases where literal characters are needed.

| Pattern | Type | Effect |
| :--- | :--- | :--- |
| `node_modules/` | **Directory** | Ignores the `node_modules` directory and all its contents. |
| `temp/` | **Directory** | Ignores any directory named `temp` anywhere in the tree. |
| `config.json:` | **File** | Ignores only files named `config.json`. A directory named `config.json` would **not** be ignored. |
| `tags:` | **File** | Ignores a file named `tags`. Useful for ignoring files that don't have extensions. |
| `build!/` | **Literal** | Ignores a file or directory named `build/` literally (disables the special directory meaning of `/`). |
| `archive!:` | **Literal** | Ignores a file or directory named `archive:` literally. |
| `config!/` | **Literal** | Ignores a file or directory named `config/` literally. |
| `docs/**/tmp/` | **Directory** | Ignores any `tmp` directory located anywhere inside the `docs` directory. |
| `src/*.c:` | **File** | Ignores all `.c` files directly inside the `src` directory. |
| `!important.log:` | **Negation** | The `!` at the beginning (before any path) negates the pattern (do **not** ignore). |
| `README.md!:` | **Literal** | Ignores a file named `README.md:`. |

---

## Plugins

Merger CLI features a plugin architecture. Plugins are standalone Python files that can define their own dependencies via a `REQUIREMENTS` list.

### Managing Plugins
*   **Install**: `merger --install-plugin path/to/plugin.py`
*   **List**: `merger --list-plugins`
*   **Update**: `merger --update-plugins` (Updates dependencies for all installed plugins)
*   **Uninstall**: `merger --uninstall-plugin <plugin_id>` (Automatically purges unused dependencies)

For developers looking to build plugins, see the [Merger Plugin API Documentation](../merger-plugin-api/README.md).

---

## CLI Options

| Option                   | Description                                                   |
|--------------------------|---------------------------------------------------------------|
| `INPUT_DIR_PATH`         | Root directory to scan.                                       |
| `OUTPUT_FILE_DIR_PATH`   | Directory to save the output (default: `.`).                  |
| `-e, --exporter`         | Choose the exporter strategy.                                 |
| `-i, --install-plugin`   | Install a custom parser or exporter plugin.                   |
| `-u, --uninstall-plugin` | Uninstall a plugin by ID (use `*` for all).                   |
| `-l, --list-plugins`     | List all installed custom plugins.                            |
| `--update-plugins`       | Update dependencies for all installed plugins.                |
| `--update`               | Check for CLI updates and provide download links.             |
| `--ignore`               | Glob-style patterns to ignore.                                |
| `--merger-ignore`        | Path to ignore file (default: `./merger.ignore`).             |
| `-c, --create-ignore`    | Create an ignore file from template (e.g., `PYTHON`, `RUST`). |
| `-y, --yes`              | Enable non-interactive mode (auto-confirm prompts).           |

---

## License

This project is licensed under the GPLv3 License — see [LICENSE](../../LICENSE) for details.
