from .exporter import TreeExporter
from ..entry import FileTreeEntry, FileEntry, DirectoryEntry
from ..tree import FileTree


class PlainTextExporter(TreeExporter):
    NAME = "PLAIN_TEXT"
    FILE_EXTENSION = ".txt"

    PREFIX: str = "<<FILE_START: %s>>\n"
    SUFFIX: str = "\n<<FILE_END: %s>>"

    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        return cls._serialize_entry(tree.root)

    @classmethod
    def _serialize_entry(cls, entry: FileTreeEntry) -> bytes:
        if isinstance(entry, FileEntry):
            filepath = cls._serialize_path(entry.path)
            return (
                    cls.PREFIX % filepath
                    + entry.content
                    + cls.SUFFIX % filepath
            ).encode()

        if isinstance(entry, DirectoryEntry):
            return b"\n\n".join(
                cls._serialize_entry(child)
                for child in entry.children.values()
            )

        raise TypeError(f"Unsupported entry type: {type(entry)}")

    @staticmethod
    def _serialize_path(path):
        path = path.as_posix()
        return path if path.startswith("./") or path == "." else f"./{path}"
