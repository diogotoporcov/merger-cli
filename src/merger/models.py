from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from .enums import FileTreeEntryType


class FileTreeEntry(ABC):
    """
    Abstract base class for all file tree entries.
    """


@dataclass(frozen=True)
class FileEntry(FileTreeEntry):
    name: str
    path: Path
    content: Optional[str] = None
    type: FileTreeEntryType = FileTreeEntryType.FILE


@dataclass(frozen=True)
class DirectoryEntry(FileTreeEntry):
    name: str
    path: Path
    children: Dict[Path, FileTreeEntry] = field(default_factory=dict)
    type: FileTreeEntryType = FileTreeEntryType.DIRECTORY


class FileTree:
    """
    A container for the file tree structure.
    """
    def __init__(self, root: DirectoryEntry) -> None:
        self.root = root
