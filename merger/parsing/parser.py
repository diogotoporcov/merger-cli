import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union, Set


class Parser(ABC):
    """
    Abstract base class for stateless file parsing.

    Attributes:
        EXTENSIONS: File extensions supported by this parser. Must contain at least one value.
        CHUNK_BYTES_FOR_VALIDATION: Number of bytes required to validate a file.
            If None, the entire file must be read for validation.
    """

    EXTENSIONS: Set[str]
    CHUNK_BYTES_FOR_VALIDATION: Optional[int] = 1024

    def __new__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} is a stateless strategy and must not be instantiated")

    @classmethod
    @abstractmethod
    def validate(
            cls,
            file_chunk_bytes: Union[bytes, bytearray],
            *,
            file_path: Optional[Path] = None,
            logger: Optional[logging.Logger] = None
    ) -> bool:
        """
        Validate that the given file bytes represent a supported and readable file.

        Args:
            file_chunk_bytes: Binary contents of the file being validated.
            file_path: Optional path to the file being validated.
            logger: Optional logger instance.

        Returns:
            bool: True if the file is valid for this parser, False otherwise.
        """
        pass

    @classmethod
    @abstractmethod
    def parse(
            cls,
            file_bytes: Union[bytes, bytearray],
            *,
            file_path: Optional[Path] = None,
            logger: Optional[logging.Logger] = None
    ) -> str:
        """
        Parse a validated file and return its extracted text content.

        Args:
            file_bytes: Full binary contents of the file.
            file_path: Optional path to the source file.
            logger: Optional logger instance.

        Returns:
            str: Parsed text content.
        """
        pass
