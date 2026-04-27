from pathlib import Path
from typing import Union, Optional

import pymupdf
from merger.parsing.base import Parser
from merger.parsing.registry import parser_registry


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
            with pymupdf.open(stream=file_chunk_bytes) as doc:
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
        texts = []
        with pymupdf.open(stream=file_bytes) as doc:
            for page in doc:
                text = page.get_text()
                if text:
                    text = text.replace("\n\n", "")
                    texts.append(text)

        full_text = " ".join(texts)
        return full_text
