from .text import TextExporter
from .tree import TreeStructureExporter
from ..base import TreeExporter
from ..registry import exporter_registry
from ...models import FileTree


@exporter_registry.register(name="TREE_TEXT", extension=".txt")
class TreeTextExporter(TreeExporter):
    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        separator = b"\n\n"

        tree_bytes = TreeStructureExporter.export(tree)
        plain_text_bytes = TextExporter.export(tree)

        return tree_bytes + separator + plain_text_bytes
