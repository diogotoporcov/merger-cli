# Merger CLI & Plugin API

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/merger-plugin-api.svg?color=orange)](https://pypi.org/project/merger-plugin-api/)

Merger is a **command-line utility** for developers that **scans a directory**, **filters files** using customizable ignore patterns, and **merges all readable content** into a **single output file**, suitable both for **human reading** and for **use by AI models**.

It supports **multiple output formats** (e.g., JSON, directory tree, plain text with file delimiters), and can be extended with **custom file parsers** (e.g., `.pdf`) and **custom exporters** (e.g., `.xml`, `.md`).

This repository is a monorepo containing:
- **`merger-cli`**: The main command-line tool.
- **`merger-plugin-api`**: A lightweight library for building custom plugins.

---

## Merger CLI

The `merger-cli` is the primary tool for scanning and merging your project files. It is distributed as standalone binaries, meaning you don't even need Python installed to use it.

### Quick Start (CLI)

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

### CLI Features
* **Recursive merge** of all readable files under a root directory.
* **Custom glob-like ignore patterns** with specialized type qualifiers.
* **Intelligent plugin system**: SQLite-backed tracking with automatic dependency management via `uv`.
* **Automatic file encoding detection**.
* **Multiple export formats**: Built-in support for Plain Text, JSON, Directory Trees, and more.
* **Modern CLI interface**: Update notifications and non-interactive mode.

For detailed CLI documentation, installation methods, and usage guides, see the [Merger CLI README](packages/merger-cli/README.md).

---

## Merger Plugin API

The `merger-plugin-api` is a lightweight library that provides interfaces and data models for extending `merger-cli`. It allows developers to build custom parsers (to read non-text files) and custom exporters (to output data in any format).

### Quick Start (API)

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
           # The name of the parser (used in --install-plugin argument)
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

### API Features
- **Abstract base classes** for custom Parsers and Exporters.
- **Data models** for the File Tree structure (`FileTree`, `FileEntry`, `DirectoryEntry`).
- **Dependency tracking**: Define a `REQUIREMENTS` list in your plugin, and the CLI will handle the installation.

For detailed documentation, implementation examples (like PDF parsers or Markdown exporters), and data model definitions, see the [Merger Plugin API README](packages/merger-plugin-api/README.md).

---

## License

This project is licensed under the GPLv3 License — see [LICENSE](LICENSE) for details.
