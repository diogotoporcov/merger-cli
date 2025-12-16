from abc import ABC, abstractmethod

from ..tree import FileTree


class TreeExporter(ABC):
    """
    Strategy interface for exporting a FileTree to a custom format.
    """

    NAME: str
    FILE_EXTENSION: str

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} must not be instantiated")

    @classmethod
    @abstractmethod
    def export(cls, tree: FileTree) -> bytes:
        """
        Export the given FileTree into a custom representation.
        """
        pass
