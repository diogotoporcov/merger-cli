from pathlib import Path
from typing import Dict, Optional, Sequence

from ..logging import logger
from ..models import DirectoryEntry, FileTreeEntry, FileEntry, FileTree
from ..parsing.registry import get_parser
from ..utils.patterns import compile_patterns, matches_any_pattern, PatternSpec


class FileTreeScanner:
    """
    Logic for scanning the file system and building a FileTree.
    """

    @classmethod
    def scan(
            cls,
            path: Path,
            ignore_patterns: Optional[Sequence[str]] = None,
            include_content: bool = True,
    ) -> FileTree:
        if not path.is_dir():
            raise NotADirectoryError(f"{path} is not a directory")

        root_path = path.resolve()
        spec = compile_patterns(ignore_patterns or [])

        root_entry = cls._scan_and_parse(root_path, root_path, spec, include_content)

        if not isinstance(root_entry, DirectoryEntry):
            raise RuntimeError(f"Failed to parse the root directory: {root_path}")

        return FileTree(root_entry)

    @classmethod
    def _scan_and_parse(
            cls,
            path: Path,
            root: Path,
            spec: PatternSpec,
            include_content: bool,
            is_dir: Optional[bool] = None,
    ) -> Optional[FileTreeEntry]:
        if is_dir is None:
            is_dir = path.is_dir()

        if path != root and matches_any_pattern(path, root, spec, is_dir=is_dir):
            return None

        rel_path = path.relative_to(root) if path != root else Path(".")

        if is_dir:
            children: Dict[Path, FileTreeEntry] = {}
            try:
                # Sort entries: directories first, then files
                entries = sorted(
                    ((entry_path, entry_path.is_dir()) for entry_path in path.iterdir()),
                    key=lambda entry: (not entry[1], entry[0].name.lower())
                )
            except PermissionError:
                logger.warning(f"Permission denied: {path}")
                entries = []

            for entry_path, entry_is_dir in entries:
                child_entry = cls._scan_and_parse(
                    entry_path,
                    root,
                    spec,
                    include_content,
                    is_dir=entry_is_dir,
                )
                if child_entry is not None:
                    children[child_entry.path] = child_entry

            return DirectoryEntry(
                name=path.name,
                path=rel_path,
                children=children
            )

        if not include_content:
            return FileEntry(
                name=path.name,
                path=rel_path,
            )

        parser = get_parser(path.name)
        max_bytes = getattr(parser, "MAX_BYTES_FOR_VALIDATION", 1024)
        try:
            with path.open("rb") as file:
                if max_bytes is None:
                    file_bytes = file.read()
                    validation_bytes = file_bytes
                else:
                    validation_bytes = file.read(max_bytes)

                if not parser.validate(validation_bytes, path):
                    return None

                if max_bytes is not None:
                    if len(validation_bytes) == max_bytes:
                        file_bytes = validation_bytes + file.read()
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
