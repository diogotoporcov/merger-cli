import logging
from pathlib import Path
from typing import Union, Tuple, Optional

import charset_normalizer
import magic

from ..parser import Parser


class DefaultParser(Parser):
    EXTENSIONS = None

    MAX_BYTES_FOR_VALIDATION: Optional[int] = 1024

    TEXT_CONFIDENCE_THRESHOLD = 0.8
    MAX_BINARY_RATIO = 0.30

    TEXTUAL_APPLICATION_MIMES = {
        # JSON (files)
        "application/json",
        "application/ld+json",
        "application/vnd.api+json",

        # XML-based files (configs, documents, feeds)
        "application/xml",
        "application/xhtml+xml",
        "application/atom+xml",
        "application/rss+xml",
        "application/soap+xml",
        "application/xml-dtd",

        # YAML (config files)
        "application/yaml",
        "application/x-yaml",

        # TOML (config files)
        "application/toml",
        "application/x-toml",

        # Forms / encoded text files
        "application/x-www-form-urlencoded",

        # JavaScript files (yes, real files)
        "application/javascript",

        # Script / source files
        "application/x-sh",
        "application/x-bash",
        "application/x-csh",
        "application/x-python",

        # Text-based document format
        "application/rtf",

        # Patch / diff files (VERY common in repos)
        "application/vnd.github.v3.diff",
        "application/vnd.github.v3.patch",

        # Edge but legit text configs
        "application/graphql",

        # Empty files
        "application/x-empty",
        "inode/x-empty",
    }

    @staticmethod
    def guess_encoding(file_chunk: Union[bytes, bytearray]) -> Tuple[str, float]:
        result = charset_normalizer.from_bytes(file_chunk).best()
        if result:
            return result.encoding, result.coherence
        return "utf-8", 0.0

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

        # Count non-printable ASCII characters (excluding standard whitespaces like tab, LF, FF, CR).
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
                    logger.debug(f"Rejected by MIME type: {mime_type} for {file_path}")
                return False

        if cls.looks_binary(file_chunk_bytes):
            if logger:
                logger.debug(f"Binary signature detected for {file_path}")
            return False

        encoding, confidence = cls.guess_encoding(file_chunk_bytes)

        if confidence < cls.TEXT_CONFIDENCE_THRESHOLD and logger:
            logger.debug(
                f"Low encoding confidence ({confidence}) for {file_path}"
            )

        try:
            file_chunk_bytes.decode(encoding)
            return True
            
        except (UnicodeDecodeError, LookupError):
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

        except (UnicodeDecodeError, LookupError):
            if logger:
                logger.debug(
                    f"Decoding failed for {file_path}, falling back to utf-8"
                )

            return file_bytes.decode("utf-8", errors="backslashreplace")
