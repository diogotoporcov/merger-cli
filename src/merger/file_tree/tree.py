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

        root_entry = cls._scan_and_parse(root_path, root_path, spec)

        if not isinstance(root_entry, DirectoryEntry):
            raise RuntimeError(f"Failed to parse the root directory: {root_path}")

        return cls(root_entry)

    @classmethod
    def _scan_and_parse(
            cls,
            path: Path,
            root: Path,
            spec: PatternSpec
    ) -> Optional[FileTreeEntry]:
        from ..utils.files import read_file_bytes

        if path != root and matches_any_pattern(path, root, spec):
            return None

        rel_path = path.relative_to(root) if path != root else Path(".")

        if path.is_dir():
            children: Dict[Path, FileTreeEntry] = {}
            try:
                # Sort entries: directories first, then files
                entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except PermissionError:
                logger.warning(f"Permission denied: {path}")
                entries = []

            for entry_path in entries:
                child_entry = cls._scan_and_parse(entry_path, root, spec)
                if child_entry is not None:
                    children[child_entry.path] = child_entry

            return DirectoryEntry(
                name=path.name,
                path=rel_path,
                children=children
            )

        parser = get_parser(path.name)
        try:
            validation_bytes = read_file_bytes(path, parser.MAX_BYTES_FOR_VALIDATION)
            if not parser.validate(validation_bytes, path):
                return None

            if parser.MAX_BYTES_FOR_VALIDATION is not None:
                file_bytes = read_file_bytes(path)
            else:
                file_bytes = validation_bytes

            content = parser.parse(file_bytes, path)
            return FileEntry(
                name=path.name,
                path=rel_path,
                content=content
            )
        except (PermissionError, OSError) as e:
            logger.warning(f"Could not process file {path}: {e}")
            return None
