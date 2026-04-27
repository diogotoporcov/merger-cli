from dataclasses import dataclass
from typing import Type, Protocol, runtime_checkable

from .models import FileTree


@runtime_checkable
class TreeExporter(Protocol):
    """
    Strategy interface for exporting a FileTree to a custom format.
    """

    @classmethod
    def export(cls, tree: FileTree) -> bytes:
        """
        Export the given FileTree into a custom representation.
        """
        ...


@dataclass(frozen=True)
class ExporterInfo:
    """
    Metadata about an exporter implementation.
    """
    cls: Type[TreeExporter]
    name: str
    file_extension: str
