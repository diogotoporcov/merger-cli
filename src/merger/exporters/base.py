from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

from ..models import FileTree


class TreeExporter(ABC):
    """
    Strategy interface for exporting a FileTree to a custom format.
    """

    @classmethod
    @abstractmethod
    def export(cls, tree: FileTree) -> bytes:
        """
        Export the given FileTree into a custom representation.
        """


@dataclass(frozen=True)
class ExporterInfo:
    """
    Metadata about an exporter implementation.
    """
    cls: Type[TreeExporter]
    name: str
    file_extension: str
