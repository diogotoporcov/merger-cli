from enum import Enum


class FileTreeEntryType(str, Enum):
    FILE = "FILE"
    DIRECTORY = "DIRECTORY"

    def __str__(self) -> str:
        return self.value
