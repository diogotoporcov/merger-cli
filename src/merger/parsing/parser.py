from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union, Set


class Parser(ABC):
    """
    Strategy interface for file parsing.

    Attributes:
        MAX_BYTES_FOR_VALIDATION: Max number of bytes required to validate a file.
            If None, all bytes will be used for validation.
    """

    MAX_BYTES_FOR_VALIDATION: Optional[int] = 1024

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} must not be instantiated")

    @classmethod
    @abstractmethod
    def validate(
            cls,
            file_chunk_bytes: Union[bytes, bytearray],
            file_path: Path
    ) -> bool:
        """
        Validate that the given file bytes represent a supported and readable file.

        Args:
            file_chunk_bytes: Binary contents of the file being validated.
            file_path: Path to the file being validated.

        Returns:
            bool: True if the file is valid for this parser, False otherwise.
        """
        pass

    @classmethod
    @abstractmethod
    def parse(
            cls,
            file_bytes: Union[bytes, bytearray],
            file_path: Path
    ) -> str:
        """
        Parse a validated file and return its extracted text content.

        Args:
            file_bytes: Full binary contents of the file.
            file_path: Path to the source file.

        Returns:
            str: Parsed text content.
        """
        pass
