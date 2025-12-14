import logging
from pathlib import Path
from typing import Union, Tuple, Optional

import chardet
import filetype

from .parser import Parser


class DefaultParser(Parser):
    EXTENSIONS = None

    CHUNK_BYTES_FOR_VALIDATION: Optional[int] = 1024

    TEXT_CONFIDENCE_THRESHOLD = 0.8
    MAX_BINARY_RATIO = 0.30

    TEXTUAL_APPLICATION_MIMES = {
        "application/json",
        "application/xml",
        "application/javascript",
        "application/x-yaml",
    }

    @staticmethod
    def guess_encoding(file_chunk: Union[bytes, bytearray]) -> Tuple[str, float]:
        result = chardet.detect(file_chunk)
        return (
            result.get("encoding") or "utf-8",
            result.get("confidence", 0.0)
        )

    @staticmethod
    def guess_mime_type(file_chunk: Union[bytes, bytearray]) -> Optional[str]:
        try:
            kind = filetype.guess(file_chunk)
            return kind.mime if kind else None

        except Exception:
            return None

    @staticmethod
    def looks_binary(file_chunk: Union[bytes, bytearray]) -> bool:
        if b"\x00" in file_chunk:
            return True

        non_printable = sum(
            byte < 9 or (13 < byte < 32)
            for byte in file_chunk
        )

        return (non_printable / max(len(file_chunk), 1)) > DefaultParser.MAX_BINARY_RATIO

    @classmethod
    def validate(
        cls,
        file_chunk_bytes: Union[bytes, bytearray],
        *,
        file_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ) -> bool:
        mime_type = cls.guess_mime_type(file_chunk_bytes)

        if mime_type:
            is_text_mime = (
                mime_type.startswith("text/")
                or mime_type in cls.TEXTUAL_APPLICATION_MIMES
            )

            if not is_text_mime:
                if logger:
                    logger.debug(f"Rejected by MIME type: {mime_type}")
                return False

        if cls.looks_binary(file_chunk_bytes):
            if logger:
                logger.debug("Binary signature detected")
            return False

        encoding, confidence = cls.guess_encoding(file_chunk_bytes)

        if confidence < cls.TEXT_CONFIDENCE_THRESHOLD and logger:
            logger.debug(
                f"Low encoding confidence ({confidence}) for {file_path}"
            )

        try:
            file_chunk_bytes.decode(encoding)
            return True

        except UnicodeDecodeError:
            return False

    @classmethod
    def parse(
        cls,
        file_bytes: Union[bytes, bytearray],
        *,
        file_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ) -> str:
        encoding, _ = cls.guess_encoding(file_bytes[:2048])

        try:
            return file_bytes.decode(encoding)

        except UnicodeDecodeError:
            if logger:
                logger.debug(
                    f"Decoding failed for {file_path}, falling back to utf-8"
                )

            return file_bytes.decode("utf-8", errors="backslashreplace")
