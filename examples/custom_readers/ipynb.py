import json
from pathlib import Path
from typing import Final, Callable

import chardet


def is_ipynb_file(file_path: Path) -> bool:
    """
    Checks whether the given file is a valid Jupyter Notebook (.ipynb) file.

    Args:
        file_path (Path): Path to the file.

    Returns:
        bool: True if the file is a readable notebook with at least one cell, False otherwise.
    """
    try:
        if not file_path.suffix == ".ipynb":
            return False

        with open(file_path, "rb") as file:
            chunk = file.read(1024)

        result = chardet.detect(chunk)
        encoding = result.get("encoding")
        confidence = result.get("confidence", 0)

        if not encoding or confidence < 0.8:
            encoding = "utf-8"

        with file_path.open(encoding=encoding) as f:
            notebook = json.load(f)

        return isinstance(notebook, dict) and "cells" in notebook and isinstance(notebook["cells"], list)

    except Exception:
        return False


def extract_ipynb_content(file_path: Path, include_markdown: bool = True, include_code: bool = True) -> str:
    """
    Extracts code and markdown content from a Jupyter Notebook (.ipynb) file.

    Args:
        file_path (Path): Path to the notebook file.
        include_markdown (bool): Whether to include markdown cells.
        include_code (bool): Whether to include code cells.

    Returns:
        str: Extracted content with cells separated by double newlines.
    """
    result = []

    with file_path.open(encoding="utf-8") as f:
        notebook = json.load(f)

    for cell in notebook.get("cells", []):
        cell_type = cell.get("cell_type")
        lines = cell.get("source", [])

        if isinstance(lines, str):
            lines = lines.splitlines()

        if cell_type == "code" and include_code:
            block = [line.rstrip() for line in lines]
            if block:
                result.append("\n".join(block))

        elif cell_type == "markdown" and include_markdown:
            block = [line.rstrip() for line in lines]
            if block:
                result.append("```markdown\n" + "\n".join(block) + "\n```")

    return "\n\n".join(result)


validator: Final[Callable[[Path], bool]] = is_ipynb_file
reader: Final[Callable[[Path], str]] = extract_ipynb_content


__all__ = ["validator", "reader"]
