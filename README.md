# Merger CLI

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/merger-api.svg?color=orange)](https://pypi.org/project/merger-api/)

Merger is a **command-line utility** for developers that **scans a directory**, **filters files** using customizable ignore patterns, and **merges all readable content** into a **single output file**, suitable both for **human reading** and for **use by AI models**.
It supports **multiple output formats** (e.g., JSON, directory tree, plain text with file delimiters), and can be extended with **custom file parsers** (e.g., `.pdf`) and **custom exporters** (e.g., `.xml`, `.md`).

---

## TLDR

1.  **Install Python 3.8 or newer**
2.  **Create and activate a virtual environment**: (If you want the CLI to be available globally, see [Global Installation](#global-installation))
    *   **Windows**: `python -m venv .venv && .venv\Scripts\activate`
    *   **Linux/macOS**: `python3 -m venv .venv && source .venv/bin/activate`
3.  **Install libmagic** if not installed:
    *   **Windows**: Automatically downloaded
    *   **Linux**: `sudo apt-get update && sudo apt-get install libmagic1`  
    *   **macOS**: `brew install libmagic`
4.  **Install the API**: `pip install merger-api` (Note: The CLI is now distributed as standalone binaries or installed from source).
5.  **Verify the installation**: `merger --version`
6.  **Navigate to your project folder**: `cd path/to/your/project`
7.  **Create a merger ignore file**: Manually or with `merger -c [TEMPLATE]` (See [Custom Ignore Templates](#custom-ignore-templates))
8.  **Execute merger-cli**: `merger .` to create a single combined file called `merger.txt`

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

### Installation from Source (Recommended for Developers)

1. Clone the repository:
    ```bash
    git clone https://github.com/diogotoporcov/merger-cli.git
    cd merger-cli
    ```

2. Install the API first:
    ```bash
    pip install -e ./src/merger-api
    ```

3. Install the CLI in editable mode:
    ```bash
    pip install -e .
    ```

4. Verify the installation:
    ```bash
    merger --version
    ```

### Global Installation

For a professional, zero-dependency experience, it is recommended to use the **Standalone Installers**.

If you still prefer to use **pipx** from source:
```bash
pipx install .
```

### Standalone Installation (No Python Required)

For a professional, zero-dependency experience, you can download standalone installers from the [GitHub Releases](https://github.com/diogotoporcov/merger-cli/releases) page. These bundles include their own Python interpreter and `pip`.

#### Windows
Download and run the `merger-cli-windows-installer.exe`. This will automatically add `merger` to your system PATH.

#### Linux (.deb / Ubuntu / Debian)
Download the `merger-cli.deb` and install it:
```bash
sudo apt install ./merger-cli.deb
```
This will also install the necessary `libmagic1` dependency.

#### macOS (Homebrew)
You can install via Homebrew by tapping the official repository (if available) or using the released tarball:
```bash
brew install diogotoporcov/merger-cli/merger-cli
```
Alternatively, download `merger-cli-macos.tar.gz`, extract it, and move the `merger` binary to your `/usr/local/bin`.

#### Managing Dependencies in Standalone Mode
Since standalone bundles are isolated, you can't use your system's `pip` to add dependencies. Use the built-in injection commands instead:
```bash
# Inject specific packages
merger --inject pymupdf "pydantic>=2.0"

# Inject from a requirements file
merger --inject-package --install-package-file requirements.txt

# Purge all injected packages
merger --purge-packages

# Update injected packages to the latest versions
merger --update-injected
```

### Updating merger-cli

To update the tool itself to the latest version:
```bash
merger --update
```
This command is context-aware:
- **Pip/Pipx**: Automatically executes the correct upgrade command.
- **Standalone**: Directs you to the GitHub releases page for the latest installer.

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

### Custom Modules and `merger-api`

If you want to extend `merger-cli` with custom parsers or exporters, you should use the `merger-api` package. This package provides the necessary interfaces and data models without the full overhead of the CLI tool.

For detailed documentation and examples on how to create custom modules, please refer to the [Merger API Documentation](src/merger-api/README.md).

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

For instructions on how to implement your own parser, see the [Merger API Documentation](src/merger-api/README.md).

### Managing Custom Modules

To install a custom module (parser or exporter):
```bash
merger --install path/to/module.py
```

To list all installed modules:
```bash
merger --list
```

To uninstall a module by its ID:
```bash
merger --uninstall <module_id>
```
*(Use `*` to uninstall all custom modules)*

---

## Custom Exporters

You can also extend Merger with **custom export strategies** to output data in any format (e.g., XML, Markdown, CSV).

For instructions on how to implement your own exporter, see the [Merger API Documentation](src/merger-api/README.md).

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
