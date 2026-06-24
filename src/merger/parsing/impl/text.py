import mimetypes
from pathlib import Path
from typing import ClassVar, FrozenSet, Optional, Tuple, Union

import charset_normalizer
import magic

from ..base import Parser


class TextParser(Parser):
    MAX_BYTES_FOR_VALIDATION: ClassVar[Optional[int]] = 1024

    TEXT_CONFIDENCE_THRESHOLD: ClassVar[float] = 0.8
    MAX_BINARY_RATIO: ClassVar[float] = 0.30
    FALLBACK_ENCODINGS: ClassVar[Tuple[str, ...]] = ("cp1252", "latin-1")

    TEXT_EXTENSIONS: ClassVar[FrozenSet[str]] = frozenset({
        ".bat",
        ".c",
        ".cfg",
        ".conf",
        ".cpp",
        ".cs",
        ".css",
        ".csv",
        ".dockerignore",
        ".env",
        ".go",
        ".gradle",
        ".gradle.kts",
        ".h",
        ".hpp",
        ".html",
        ".ini",
        ".java",
        ".js",
        ".json",
        ".jsx",
        ".kt",
        ".kts",
        ".log",
        ".md",
        ".pbtxt",
        ".properties",
        ".py",
        ".rb",
        ".rs",
        ".sh",
        ".sql",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    })

    TEXTUAL_APPLICATION_MIMES: ClassVar[FrozenSet[str]] = frozenset({
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

        # JavaScript files
        "application/javascript",

        # Script / source files
        "application/x-sh",
        "application/x-bash",
        "application/x-csh",
        "application/x-python",

        # Text-based document format
        "application/rtf",

        # Patch / diff files
        "application/vnd.github.v3.diff",
        "application/vnd.github.v3.patch",

        # Empty files
        "application/x-empty",
        "inode/x-empty",
    })

    @classmethod
    def is_text_mime(cls, mime_type: str) -> bool:
        return (
            mime_type.startswith("text/")
            or mime_type in cls.TEXTUAL_APPLICATION_MIMES
        )

    @classmethod
    def is_known_text_path(cls, file_path: Path) -> bool:
        suffixes = [suffix.lower() for suffix in file_path.suffixes]
        if any(suffix in cls.TEXT_EXTENSIONS for suffix in suffixes):
            return True

        return "".join(suffixes) in cls.TEXT_EXTENSIONS

    @staticmethod
    def guess_encoding(file_chunk: Union[bytes, bytearray]) -> Tuple[str, float]:
        result = charset_normalizer.from_bytes(file_chunk).best()
        if result:
            return result.encoding, result.coherence
        return "utf-8", 0.0

    @classmethod
    def decode_text(cls, file_bytes: Union[bytes, bytearray]) -> str:
        try:
            return file_bytes.decode("utf-8")

        except UnicodeDecodeError:
            pass

        for encoding in cls.FALLBACK_ENCODINGS:
            try:
                return file_bytes.decode(encoding)

            except (UnicodeDecodeError, LookupError):
                continue

        return file_bytes.decode("utf-8", errors="backslashreplace")

    @staticmethod
    def guess_mime_type(
        file_chunk: Union[bytes, bytearray],
        file_path: Path
    ) -> Optional[str]:
        from ...logging import logger
        mime = None
        try:
            guess, _ = mimetypes.guess_type(file_path)
            if guess and TextParser.is_text_mime(guess):
                return guess
        except Exception as e:
            logger.debug(f"mimetypes fallback failed for {file_path}: {e}")

        if TextParser.is_known_text_path(file_path):
            return "text/plain"

        try:
            mime = magic.from_buffer(file_chunk, mime=True)
        except Exception as e:
            logger.debug(f"libmagic failed for {file_path}: {e}")

        if not mime or mime == "application/octet-stream":
            try:
                guess, _ = mimetypes.guess_type(file_path)
                if guess:
                    mime = guess
            except Exception as e:
                logger.debug(f"mimetypes fallback failed for {file_path}: {e}")

        if not mime or mime == "application/octet-stream":
            if TextParser.looks_binary(file_chunk):
                mime = "application/octet-stream"
            else:
                mime = "text/plain"

        return mime

    @staticmethod
    def looks_binary(file_chunk: Union[bytes, bytearray]) -> bool:
        if b"\x00" in file_chunk:
            return True

        # Count non-printable ASCII characters (excluding standard whitespaces like tab, LF, FF, CR).
        non_printable = sum(
            byte < 9 or (13 < byte < 32)
            for byte in file_chunk
        )

        return (non_printable / max(len(file_chunk), 1)) > TextParser.MAX_BINARY_RATIO

    @classmethod
    def validate(
        cls,
        file_chunk_bytes: Union[bytes, bytearray],
        file_path: Path
    ) -> bool:
        if cls.looks_binary(file_chunk_bytes):
            return False

        mime_type = cls.guess_mime_type(file_chunk_bytes, file_path=file_path)

        if mime_type:
            if not cls.is_text_mime(mime_type):
                return False

        try:
            cls.decode_text(file_chunk_bytes)
            return True

        except (UnicodeDecodeError, LookupError):
            return False

    @classmethod
    def parse(
        cls,
        file_bytes: Union[bytes, bytearray],
        file_path: Path
    ) -> str:
        return cls.decode_text(file_bytes)
