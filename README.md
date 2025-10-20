# Merger CLI

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Merger is a command-line utility for developers that scans a directory, filters files using customizable ignore patterns, and merges all readable content into a single structured output file. It supports custom file readers and validators, making it easily extendable for formats such as `.ipynb`, `.pdf`, or any specific format.

---

## Summary

1. [Core Features](#core-features)
2. [Dependencies](#dependencies)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Custom Readers](#custom-readers)
6. [CLI Options](#cli-options)
7. [License](#license)

---

## Core Features

* **Recursive merge** of all readable text files under a root directory.
* **Glob-based ignore patterns** using `.gitignore`-style syntax.
* **Automatic encoding detection**.
* **Custom file readers and validators** for non-text formats.
* **CLI support** for installation, removal, and listing of custom readers.
* **Human-readable merged output**, including a directory tree header and file delimiters.

---

## Dependencies

| Component   | Version / Type | Notes                       |
|-------------|----------------|-----------------------------|
| **Python**  | ≥ 3.8          | Required                    |

All dependencies are listed in [`requirements.txt`](requirements.txt).

---

## Installation

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

This registers the `merger` command globally.

---

## Usage

### Basic merge

```bash
merger ./src ./merged.txt
```

### Custom ignore patterns

```bash
merger "C:\Users\USER\Desktop\project" "C:\Users\USER\Desktop\project\output.txt" --ignore "*.log" "__pycache__" "*.tmp"
```

### Custom ignore file

```bash
merger . ./output.txt -p ./merger.ignore
```

### Include empty files

```bash
merger ./data ./output.txt --empty
```

### Verbose output

```bash
merger ./src ./merged.txt --log-level DEBUG
```

---

## Custom Readers

You can extend Merger to handle new file formats.

### Installing a custom reader

```bash
merger --install .ipynb path/to/ipynb.py
```

Where `ipynb.py` must define:

*   ```python
    validator: Callable[[Path], bool]
    ```
*   ```python
    reader: Callable[[Path], str]
    ```

To uninstall:

```bash
merger --uninstall .ipynb
```

List installed readers:

```bash
merger --list-installed
```

An example `.ipynb` reader can be found in
[`examples/custom_readers/ipynb.py`](examples/custom_readers/ipynb.py).

---

## CLI Options

| Option                  | Description                                                                    |
|-------------------------|--------------------------------------------------------------------------------|
| `--ignore`              | List of glob-style ignore patterns.                                            |
| `-f, --ignore-file`     | Path to file containing ignore patterns (Default: `<input_dir>/merger.ignore`. |
| `-i, --install`         | Install a custom reader for an extension.                                      |
| `-u, --uninstall`       | Remove a custom reader (`*` removes all).                                      |
| `--list-installed`      | Show installed readers.                                                        |
| `-l, --log-level`       | Set logging verbosity (`DEBUG`, `INFO`, etc.).                                 |
| `--empty`               | Include empty files in merged output.                                          |
| `--prefix` / `--suffix` | Customize file delimiters in output.                                           |
| `--overrides`           | Load override reader definitions from a Python module.                         |
| `--no-tree`             | Do not include the generated directory tree in the output file.                |


---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
