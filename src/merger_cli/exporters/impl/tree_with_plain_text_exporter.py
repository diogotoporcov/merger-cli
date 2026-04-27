from .directory_tree_exporter import DirectoryTreeExporter
from .plain_text_exporter import PlainTextExporter
from ...api import TreeExporter


NAME = "TREE_PLAIN_TEXT"
FILE_EXTENSION = ".txt"


class TreeWithPlainTextExporter(TreeExporter):
    @classmethod
    def export(cls, tree) -> bytes:
        separator = b"\n\n"

        tree_bytes = DirectoryTreeExporter.export(tree)
        plain_text_bytes = PlainTextExporter.export(tree)

        return tree_bytes + separator + plain_text_bytes
