from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, List


class Parser(ABC):
    """
    Strategy interface for file parsing.
    """

    EXTENSIONS: List[str]
    MAX_BYTES_FOR_VALIDATION: int = 1024

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
