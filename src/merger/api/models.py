from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, TypeVar, Protocol, runtime_checkable

from .enums import FileTreeEntryType

T = TypeVar("T", bound="FileTree")


@runtime_checkable
class FileTreeEntry(Protocol):
    @property
    def type(self) -> FileTreeEntryType: ...

    @property
    def name(self) -> str: ...

    @property
    def path(self) -> Path: ...


@dataclass(frozen=True)
class FileEntry:
    name: str
    path: Path
    content: Optional[str] = None
    type: FileTreeEntryType = FileTreeEntryType.FILE


@dataclass(frozen=True)
class DirectoryEntry:
    name: str
    path: Path
    children: Dict[Path, "FileTreeEntry"] = field(default_factory=dict)
    type: FileTreeEntryType = FileTreeEntryType.DIRECTORY


class FileTree:
    """
    A container for the file tree structure.
    """
    def __init__(self, root: DirectoryEntry) -> None:
        self.root = root
