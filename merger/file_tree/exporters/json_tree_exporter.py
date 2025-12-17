import json

from ..tree import FileTree
from .tree_exporter import TreeExporter
from ..entry import DirectoryEntry, FileEntry, FileTreeEntry


class JsonTreeExporter(TreeExporter):
    NAME = "JSON_TREE"
    FILE_EXTENSION = ".json"

    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        return json.dumps(
            cls._serialize_entry(tree.root),
            indent=2,
            ensure_ascii=False
        ).encode()

    @classmethod
    def _serialize_entry(cls, entry: FileTreeEntry):
        if isinstance(entry, FileEntry):
            return {
                "type": entry.type.value.lower(),
                "path": cls._serialize_path(entry.path),
                "content": entry.content,
            }

        if isinstance(entry, DirectoryEntry):
            children = sorted(
                entry.children.values(),
                key=lambda e: e.path.as_posix().lower()
            )

            return {
                "type": entry.type.value.lower(),
                "path": cls._serialize_path(entry.path),
                "children": {
                    child.name: cls._serialize_entry(child)
                    for child in children
                },
            }

        raise TypeError(f"Unsupported entry type: {type(entry)}")

    @staticmethod
    def _serialize_path(path):
        path = path.as_posix()
        return path if path.startswith("./") or path == "." else f"./{path}"
