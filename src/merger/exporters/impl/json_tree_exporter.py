from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Literal, Optional, TypedDict, Union

from ..base import TreeExporter
from ..registry import exporter_registry
from ...models import FileTree, DirectoryEntry, FileEntry, FileTreeEntry


class SerializedFileEntry(TypedDict):
    type: Literal["file"]
    path: str
    content: Optional[str]


class SerializedDirectoryEntry(TypedDict):
    type: Literal["directory"]
    path: str
    children: Dict[str, SerializedEntry]


SerializedEntry = Union[SerializedFileEntry, SerializedDirectoryEntry]


@exporter_registry.register(name="JSON_TREE", extension=".json")
class JsonTreeExporter(TreeExporter):
    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        return json.dumps(
            cls._serialize_entry(tree.root),
            indent=2,
            ensure_ascii=False
        ).encode()

    @classmethod
    def _serialize_entry(cls, entry: FileTreeEntry) -> SerializedEntry:
        if isinstance(entry, FileEntry):
            serialized_file: SerializedFileEntry = {
                "type": "file",
                "path": cls._serialize_path(entry.path),
                "content": entry.content,
            }
            return serialized_file

        if isinstance(entry, DirectoryEntry):
            children = sorted(
                entry.children.values(),
                key=lambda e: e.path.as_posix().lower()
            )

            serialized_directory: SerializedDirectoryEntry = {
                "type": "directory",
                "path": cls._serialize_path(entry.path),
                "children": {
                    child.name: cls._serialize_entry(child)
                    for child in children
                },
            }
            return serialized_directory

        raise TypeError(f"Unsupported entry type: {type(entry)}")

    @staticmethod
    def _serialize_path(path: Path) -> str:
        path = path.as_posix()
        return path if path.startswith("./") or path == "." else f"./{path}"
