from pathlib import Path
from typing import Self, Dict, List, Optional

from .entry import DirectoryEntry, FileTreeEntry, FileEntry
from ..logging.logger import logger
from ..parsing.modules import get_parser
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
        from ..utils.files import read_file_bytes

        rel_path = Path(".") if path == root else Path(".") / path.relative_to(root)
        children: Dict[Path, FileTreeEntry] = {}

        for entry_path in path.iterdir():
            path_relative = Path(".") / entry_path.relative_to(root)

            if ignore_patterns and matches_any_pattern(
                f"./{path_relative.as_posix()}",
                ignore_patterns
            ):
                continue

            if entry_path.is_dir():
                children[path_relative] = cls._build_tree(
                    entry_path,
                    root,
                    ignore_patterns
                )
                continue

            parser = get_parser(entry_path.name)
            file_bytes = read_file_bytes(
                entry_path,
                parser.MAX_BYTES_FOR_VALIDATION
            )

            if not parser.validate(
                file_bytes,
                file_path=entry_path,
                logger=logger
            ):
                continue

            if parser.MAX_BYTES_FOR_VALIDATION is not None:
                file_bytes = read_file_bytes(entry_path, None)

            children[path_relative] = FileEntry(
                name=entry_path.name,
                path=path_relative,
                content=parser.parse(
                    file_bytes,
                    file_path=entry_path,
                    logger=logger
                )
            )

        return DirectoryEntry(
            name=path.name,
            path=rel_path,
            children=children
        )
