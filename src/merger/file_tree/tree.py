from pathlib import Path
from typing import Dict, List, Optional, TypeVar, Type

from .entries import DirectoryEntry, FileTreeEntry, FileEntry
from ..logging import logger
from ..parsing.registry import get_parser
from ..utils.patterns import compile_patterns, matches_any_pattern, PatternSpec

T = TypeVar("T", bound="FileTree")


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
        spec = compile_patterns(ignore_patterns or [])

        root_entry = cls._scan_disk(root_path, root_path, spec)
        parsed_root = cls._parse_tree(root_entry, root_path)

        if not isinstance(parsed_root, DirectoryEntry):
            raise RuntimeError(f"Failed to parse the root directory: {root_path}")

        return cls(parsed_root)

    @classmethod
    def _scan_disk(
            cls,
            path: Path,
            root: Path,
            spec: PatternSpec
    ) -> DirectoryEntry:
        rel_path = path.relative_to(root) if path != root else Path(".")
        children: Dict[Path, FileTreeEntry] = {}

        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))

        except PermissionError:
            logger.warning(f"Permission denied: {path}")
            entries = []

        for entry_path in entries:
            path_relative = entry_path.relative_to(root)

            if matches_any_pattern(entry_path, root, spec):
                continue

            if entry_path.is_dir():
                children[path_relative] = cls._scan_disk(entry_path, root, spec)
                continue

            children[path_relative] = FileEntry(
                name=entry_path.name,
                path=path_relative,
                content=None
            )

        return DirectoryEntry(
            name=path.name,
            path=rel_path,
            children=children
        )

    @classmethod
    def _parse_tree(
            cls,
            entry: FileTreeEntry,
            root_path: Path
    ) -> Optional[FileTreeEntry]:
        from ..utils.files import read_file_bytes

        if isinstance(entry, DirectoryEntry):
            new_children: Dict[Path, FileTreeEntry] = {}
            for path, child in entry.children.items():
                parsed_child = cls._parse_tree(child, root_path)
                if parsed_child is not None:
                    new_children[path] = parsed_child

            return DirectoryEntry(
                name=entry.name,
                path=entry.path,
                children=new_children
            )

        if isinstance(entry, FileEntry):
            full_path = root_path / entry.path
            parser = get_parser(entry.name)

            validation_bytes = read_file_bytes(full_path, parser.MAX_BYTES_FOR_VALIDATION)
            if not parser.validate(validation_bytes, file_path=full_path, logger=logger):
                return None

            if parser.MAX_BYTES_FOR_VALIDATION is not None:
                file_bytes = read_file_bytes(full_path)
            else:
                file_bytes = validation_bytes

            content = parser.parse(file_bytes, file_path=full_path, logger=logger)
            return FileEntry(
                name=entry.name,
                path=entry.path,
                content=content
            )

        return entry
