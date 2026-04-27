import xml.etree.ElementTree as ET

from merger.api import FileEntry, DirectoryEntry, FileTreeEntry, TreeExporter, FileTree

# The name of the exporter (used in --exporter argument)
NAME = "XML"
# The extension of the output file
FILE_EXTENSION = ".xml"


class XmlExporter(TreeExporter):
    """
    A custom exporter that generates an XML representation of the file tree.
    """

    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        """
        Export the file tree into an XML representation.
        """
        root = ET.Element("filetree")
        cls._to_xml(tree.root, root)

        cls._indent(root)

        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    @classmethod
    def _to_xml(cls, entry: FileTreeEntry, parent: ET.Element):
        if isinstance(entry, FileEntry):
            file_el = ET.SubElement(parent, "file", {
                "name": entry.name,
                "path": entry.path.as_posix()
            })
            content_el = ET.SubElement(file_el, "content")
            content_el.text = entry.content

        elif isinstance(entry, DirectoryEntry):
            dir_el = ET.SubElement(parent, "directory", {
                "name": entry.name,
                "path": entry.path.as_posix()
            })
            for child in sorted(entry.children.values(), key=lambda e: e.name.lower()):
                cls._to_xml(child, dir_el)

    @classmethod
    def _indent(cls, elem: ET.Element, level: int = 0):
        """
        Recursive function to indent XML elements while preserving text content.
        """
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "

            if not elem.tail or not elem.tail.strip():
                elem.tail = i

            for child in elem:
                cls._indent(child, level + 1)

            if len(elem) > 0:
                last_child = elem[-1]
                if not last_child.tail or not last_child.tail.strip():
                    last_child.tail = i

        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

# Export the exporter class
exporter_cls = XmlExporter
