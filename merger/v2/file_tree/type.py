from enum import StrEnum, auto


class FileTreeEntryType(StrEnum):
    FILE = auto()
    DIRECTORY = auto()
