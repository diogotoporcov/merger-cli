from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

from .type import FileTreeEntryType


class FileTreeEntry(ABC):
    type: FileTreeEntryType
    name: str
    path: Path

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @abstractmethod
    def to_json_dict(self) -> dict:
        pass

    @staticmethod
    def _serialize_path(path: Path) -> str:
        p = path.as_posix()
        if p != "." and not p.startswith("./"):
            return f"./{p}"

        return p


@dataclass(frozen=True)
class FileEntry(FileTreeEntry):
    type = FileTreeEntryType.FILE
    name: str
    path: Path

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "name": self.name,
            "path": self.path,
        }

    def to_json_dict(self) -> dict:
        return {
            "type": self.type.value,
            "name": self.name,
            "path": self._serialize_path(self.path),
        }


@dataclass(frozen=True)
class DirectoryEntry(FileEntry):
    type = FileTreeEntryType.DIRECTORY
    name: str
    path: Path
    children: Dict[Path, FileTreeEntry] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "name": self.name,
            "path": self.path,
            "children": {
                child.path: child.to_dict()
                for child in self.children.values()
            },
        }

    def to_json_dict(self) -> dict:
        return {
            "type": self.type.value,
            "name": self.name,
            "path": self._serialize_path(self.path),
            "children": {
                child.name: child.to_json_dict()
                for child in self.children.values()
            },
        }
