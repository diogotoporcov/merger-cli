import importlib
from pathlib import Path
from types import ModuleType
from typing import List, Optional, Union

from merger.parsing.base import Parser
from merger.parsing.registry import parser_registry

_pymupdf: Optional[ModuleType] = None


def _get_pymupdf() -> ModuleType:
    global _pymupdf
    if _pymupdf is None:
        _pymupdf = importlib.import_module("pymupdf")
    return _pymupdf


@parser_registry.register(extensions={".pdf"})
class PdfParser(Parser):
    MAX_BYTES_FOR_VALIDATION: Optional[int] = None

    @classmethod
    def validate(
        cls,
        file_chunk_bytes: Union[bytes, bytearray],
        file_path: Path
    ) -> bool:
        """
        Validate that the given file bytes represent a readable PDF document.
        """
        try:
            pymupdf = _get_pymupdf()
            open_pdf = getattr(pymupdf, "open")
            with open_pdf(stream=file_chunk_bytes) as doc:
                _ = doc[0]
            return True

        except Exception:
            return False

    @classmethod
    def parse(
        cls,
        file_bytes: Union[bytes, bytearray],
        file_path: Path,
    ) -> str:
        """
        Extracts and concatenates text from all pages of a PDF file.
        """
        pymupdf = _get_pymupdf()
        texts: List[str] = []
        open_pdf = getattr(pymupdf, "open")
        with open_pdf(stream=file_bytes) as doc:
            for page in doc:
                text = page.get_text()
                if text:
                    text = text.replace("\n\n", "")
                    texts.append(text)

        full_text = " ".join(texts)
        return full_text
