from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from .enums import FileTreeEntryType


class FileTreeEntry(ABC):
    type: FileTreeEntryType
    name: str
    path: Path


@dataclass(frozen=True)
class FileEntry(FileTreeEntry):
    name: str
    path: Path
    content: str
    type: FileTreeEntryType = FileTreeEntryType.FILE


@dataclass(frozen=True)
class DirectoryEntry(FileTreeEntry):
    name: str
    path: Path
    children: Dict[Path, "FileTreeEntry"] = field(default_factory=dict)
    type: FileTreeEntryType = FileTreeEntryType.DIRECTORY
