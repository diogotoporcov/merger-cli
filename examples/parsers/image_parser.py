import io
from pathlib import Path
from typing import Union, Optional, Set

from PIL import Image
from easyocr import Reader

# File extensions this parser supports
EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".gif"
}


from merger.parsing.base import Parser


class ImageParser(Parser):
    """
    Parser for image files that extracts text using OCR (Optical Character Recognition).
    """
    MAX_BYTES_FOR_VALIDATION: Optional[int] = None

    _reader: Optional[Reader] = None

    @classmethod
    def _get_reader(cls) -> Reader:
        """
        Lazily initialize the EasyOCR reader.
        Note: On the first call, this will download the necessary models (~100MB+).
        """
        if cls._reader is None:
            cls._reader = Reader(['en', 'es', 'fr', 'de', 'pt', 'it', 'zh_sim', 'ja', 'ko', 'ru'])

        return cls._reader

    @classmethod
    def validate(
        cls,
        file_chunk_bytes: Union[bytes, bytearray],
        file_path: Path
    ) -> bool:
        """
        Validate that the given file bytes represent a readable image supported by Pillow.
        """
        try:
            with Image.open(io.BytesIO(file_chunk_bytes)) as img:
                img.verify()

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
        Extracts text from an image using EasyOCR.
        """
        try:
            reader = cls._get_reader()
            results = reader.readtext(bytes(file_bytes), detail=0)
            return " ".join(results).strip()

        except Exception as e:
            return f"[OCR Error in {file_path.name}]: {str(e)}"


# Export the parser class
parser_cls = ImageParser
