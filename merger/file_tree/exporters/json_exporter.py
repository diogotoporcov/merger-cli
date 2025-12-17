import json
from typing import Dict

from ..tree import FileTree
from ..entry import DirectoryEntry, FileEntry, FileTreeEntry
from .tree_exporter import TreeExporter


class JsonExporter(TreeExporter):
    NAME = "JSON"
    FILE_EXTENSION = ".json"

    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        data: Dict[str, str] = {}
        cls._serialize_entry(tree.root, data)

        return json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        ).encode()

    @classmethod
    def _serialize_entry(
        cls,
        entry: FileTreeEntry,
        out: Dict[str, str],
    ) -> None:
        if isinstance(entry, FileEntry):
            out[cls._serialize_path(entry.path)] = entry.content
            return

        if isinstance(entry, DirectoryEntry):
            children = sorted(
                entry.children.values(),
                key=lambda e: e.path.as_posix().lower()
            )

            for child in children:
                cls._serialize_entry(child, out)

            return

        raise TypeError(f"Unsupported entry type: {type(entry)}")

    @staticmethod
    def _serialize_path(path) -> str:
        path = path.as_posix()
        return path if path.startswith("./") or path == "." else f"./{path}"
