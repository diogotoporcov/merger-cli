import logging
from pathlib import Path
from typing import Union, Optional, Any, Set, Type

import fitz

from merger.parsing.parser import Parser


class PdfParser(Parser):
    EXTENSIONS: Set[str] = {".pdf"}
    CHUNK_BYTES_FOR_VALIDATION: Optional[int] = None

    @classmethod
    def validate(
        cls,
        file_chunk_bytes: Union[bytes, bytearray],
        *,
        file_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ) -> bool:
        """
        Validate that the given file represents a readable PDF document.

        Args:
            file_chunk_bytes: Binary contents of the file being validated, sufficient to perform validation.
            file_path: Path of the file being validated.
            logger: Optional logger instance for logging.

        Returns:
            bool: True if the file is a readable PDF, False otherwise.
        """
        try:
            with fitz.open(file_path) as doc:
                _ = doc[0]
            return True

        except Exception:
            return False

    @classmethod
    def parse(
        cls,
        file_bytes: Union[bytes, bytearray],
        *,
        file_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None,
    ) -> str:
        """
        Extracts and concatenates text from all pages of a PDF file.

        Args:
            file_bytes: Binary contents of the file being parsed.
            file_path: Path of the file being parsed.
            logger: ptional logger instance for logging.

        Returns:

        """
        texts = []
        with fitz.open(stream=file_bytes) as doc:
            for page in doc:
                text = page.get_text()
                if text:
                    text = text.replace("\n\n", "")
                    texts.append(text)

        full_text = " ".join(texts)
        return full_text


parser: Type[Parser] = PdfParser
