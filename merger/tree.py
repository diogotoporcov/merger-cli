from pathlib import Path
from collections import defaultdict
from typing import Dict, Union, List

_FileTree = Dict[str, Union["_FileTree", None]]


def generate_tree_visualizer(root_path: Path, paths: List[Path]) -> str:
    """
    Generates a visual tree structure of the provided paths relative to a root directory.

    Args:
        root_path (Path): The root directory.
        paths (List[Path]): List of file and directory paths relative to the root to include in the tree.

    Returns:
        str: A formatted string representing the directory structure.
    """
    root_path = root_path.resolve()

    def tree() -> _FileTree:
        return defaultdict(tree)

    file_tree: _FileTree = tree()

    for path in paths:
        try:
            relative_parts = path.resolve().relative_to(root_path).parts
        except ValueError:
            continue

        current = file_tree
        for part in relative_parts:
            current = current[part]

    def build_tree_str(d: _FileTree, prefix: str = "", current_path: Path = root_path) -> str:
        tree_str = []
        entries = sorted(d.keys())
        for i, key in enumerate(entries, 1):
            is_last = i == len(entries)
            connector = "└── " if is_last else "├── "

            full_path = current_path / key

            if full_path.is_dir():
                display_name = f"{key}/"
            else:
                display_name = key

            tree_str.append(f"{prefix}{connector}{display_name}\n")

            extension = "    " if is_last else "│   "
            tree_str.append(build_tree_str(d[key], prefix + extension, full_path))

        return "".join(tree_str)

    tree_output = f"{root_path.name}/\n{build_tree_str(file_tree)}"
    return tree_output

