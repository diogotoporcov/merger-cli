import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, Optional, Union

import chardet
import magic


class Reader(ABC):
    @classmethod
    @abstractmethod
    def validate(
            cls,
            file_chunk: Union[bytes, bytearray],
            *,
            file_path: Optional[Path],
            logger: Optional[logging.Logger]
    ) -> bool:
        pass

    @classmethod
    @abstractmethod
    def get_content(
            cls,
            file_bytes: Union[bytes, bytearray],
            *,
            file_path: Optional[Path],
            logger: Optional[logging.Logger]
    ) -> str:
        pass


class DefaultReader(Reader):
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
            return magic.from_buffer(file_chunk, mime=True)
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

        return (non_printable / max(len(file_chunk), 1)) > DefaultReader.MAX_BINARY_RATIO

    @classmethod
    def validate(
        cls,
        file_chunk: Union[bytes, bytearray],
        *,
        file_path: Optional[Path],
        logger: Optional[logging.Logger]
    ) -> bool:
        mime_type = cls.guess_mime_type(file_chunk)

        if mime_type:
            is_text_mime = (
                mime_type.startswith("text/")
                or mime_type in cls.TEXTUAL_APPLICATION_MIMES
            )

            if not is_text_mime:
                if logger:
                    logger.debug(f"Rejected by MIME type: {mime_type}")
                return False

        if cls.looks_binary(file_chunk):
            if logger:
                logger.debug("Binary signature detected")
            return False

        encoding, confidence = cls.guess_encoding(file_chunk)

        if confidence < cls.TEXT_CONFIDENCE_THRESHOLD and logger:
            logger.debug(
                f"Low encoding confidence ({confidence}) for {file_path}"
            )

        try:
            file_chunk.decode(encoding)
            return True

        except UnicodeDecodeError:
            return False

    @classmethod
    def get_content(
        cls,
        file_bytes: Union[bytes, bytearray],
        *,
        file_path: Optional[Path],
        logger: Optional[logging.Logger]
    ) -> str:
        encoding, _ = cls.guess_encoding(file_bytes[:1024])

        try:
            return file_bytes.decode(encoding)

        except UnicodeDecodeError:
            if logger:
                logger.warning(
                    f"Decoding failed for {file_path}, falling back to utf-8"
                )

            return file_bytes.decode("utf-8", errors="replace")
