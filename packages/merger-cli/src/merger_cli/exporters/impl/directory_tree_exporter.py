from merger_plugin_api import TreeExporter, FileTree, DirectoryEntry, FileTreeEntry


NAME = "TREE"
FILE_EXTENSION = ".txt"


class DirectoryTreeExporter(TreeExporter):
    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        def format_name(entry: FileTreeEntry) -> str:
            return f"{entry.name}/" if isinstance(entry, DirectoryEntry) else entry.name

        lines = [format_name(tree.root)]

        def walk(entry: DirectoryEntry, prefix: str = "") -> None:
            children = sorted(
                entry.children.values(),
                key=lambda e: (not isinstance(e, DirectoryEntry), e.name.lower())
            )

            for index, child in enumerate(children):
                is_last = index == len(children) - 1
                connector = "└── " if is_last else "├── "
                lines.append(prefix + connector + format_name(child))

                if isinstance(child, DirectoryEntry):
                    extension = "    " if is_last else "│   "
                    walk(child, prefix + extension)

        walk(tree.root)
        return "\n".join(lines).encode()
