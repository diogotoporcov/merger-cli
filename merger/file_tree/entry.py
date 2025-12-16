from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from .type import FileTreeEntryType


class FileTreeEntry(ABC):
    type: FileTreeEntryType
    name: str
    path: Path


@dataclass(frozen=True)
class FileEntry(FileTreeEntry):
    type = FileTreeEntryType.FILE
    name: str
    path: Path
    content: str


@dataclass(frozen=True)
class DirectoryEntry(FileTreeEntry):
    type = FileTreeEntryType.DIRECTORY
    name: str
    path: Path
    children: Dict[Path, FileTreeEntry] = field(default_factory=dict)
