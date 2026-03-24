from pathlib import Path
from typing import Dict, List, Optional, TypeVar, Type

T = TypeVar("T", bound="FileTree")

from .entries import DirectoryEntry, FileTreeEntry, FileEntry
from ..logging import logger
from ..parsing.registry import get_parser
from ..utils.patterns import matches_any_pattern


class FileTree:
    def __init__(self, root: DirectoryEntry) -> None:
        self.root = root

    @classmethod
    def from_path(
            cls: Type[T],
            path: Path,
            ignore_patterns: Optional[List[str]] = None
    ) -> T:
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
        from ..utils.files import read_file_bytes

        rel_path = path.relative_to(root) if path != root else Path(".")
        children: Dict[Path, FileTreeEntry] = {}

        # Sort by directory status (directories first) and then by name (case-insensitive).
        for entry_path in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            path_relative = entry_path.relative_to(root)

            if ignore_patterns and matches_any_pattern(entry_path, root, ignore_patterns):
                continue

            if entry_path.is_dir():
                children[path_relative] = cls._build_tree(entry_path, root, ignore_patterns)
                continue

            parser = get_parser(entry_path.name)
            
            validation_bytes = read_file_bytes(entry_path, parser.MAX_BYTES_FOR_VALIDATION)
            if not parser.validate(validation_bytes, file_path=entry_path, logger=logger):
                continue

            if parser.MAX_BYTES_FOR_VALIDATION is not None:
                file_bytes = read_file_bytes(entry_path)
            else:
                file_bytes = validation_bytes

            content = parser.parse(file_bytes, file_path=entry_path, logger=logger)
            children[path_relative] = FileEntry(
                name=entry_path.name,
                path=path_relative,
                content=content
            )

        return DirectoryEntry(
            name=path.name,
            path=rel_path,
            children=children
        )
