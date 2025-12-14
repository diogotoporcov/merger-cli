from pathlib import Path
from typing import Self, Dict, List, Optional

from .entry import DirectoryEntry, FileTreeEntry, FileEntry
from ..files.files import read_file_bytes
from ..parsers.modules import get_parser
from ..utils.patterns import matches_any_pattern


class FileTree:
    def __init__(self, root: DirectoryEntry) -> None:
        self.root = root

    @classmethod
    def from_path(
            cls,
            path: Path,
            ignore_patterns: Optional[List[str]] = None
    ) -> Self:
        if not path.is_dir():
            raise NotADirectoryError(f"{path} is not a directory")

        root_path = path.resolve()
        root_entry = cls._build_tree(root_path, root_path, ignore_patterns)
        return cls(root_entry)

    @classmethod
    def _build_tree(
            cls,
            path: Path,
            root: Path,
            ignore_patterns: Optional[List[str]] = None
    ) -> DirectoryEntry:
        rel_path = Path(".") if path == root else Path(".") / path.relative_to(root)
        children: Dict[Path, FileTreeEntry] = {}

        for entry_path in path.iterdir():
            path_relative = Path(".") / entry_path.relative_to(root)

            if ignore_patterns and matches_any_pattern(f"./{path_relative.as_posix()}", ignore_patterns):
                continue

            if entry_path.is_dir():
                children[path_relative] = cls._build_tree(entry_path, root, ignore_patterns)

            else:
                parser = get_parser(path.name)
                if not parser.validate(read_file_bytes(entry_path, parser.MAX_CHUNK_BYTES)):
                    continue

                children[path_relative] = FileEntry(
                    name=entry_path.name,
                    path=path_relative,
                    content=parser.parse(read_file_bytes(entry_path))
                )

        return DirectoryEntry(
            name=path.name,
            path=rel_path,
            children=children
        )

    def to_dict(self) -> dict:
        return self.root.to_dict()

    def to_json_dict(self) -> dict:
        return self.root.to_json_dict()

    def __str__(self) -> str:
        def format_name(entry: FileTreeEntry) -> str:
            return f"{entry.name}/" if isinstance(entry, DirectoryEntry) else entry.name

        lines: List[str] = [format_name(self.root)]

        def walk(entry: DirectoryEntry, prefix: str = "") -> None:
            children = sorted(
                entry.children.values(),
                key=lambda e: (isinstance(e, FileTreeEntry), e.name.lower())
            )

            for index, child in enumerate(children):
                is_last = index == len(children) - 1
                connector = "└── " if is_last else "├── "
                lines.append(prefix + connector + format_name(child))

                if isinstance(child, DirectoryEntry):
                    extension = "    " if is_last else "│   "
                    walk(child, prefix + extension)

        walk(self.root)
        return "\n".join(lines)
