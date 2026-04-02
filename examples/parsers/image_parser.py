from pathlib import Path
from typing import Union, Optional, Set, Type
import io

from PIL import Image
from easyocr import Reader
from merger_plugin_api import Parser

REQUIREMENTS = ["Pillow", "easyocr"]

EXTENSIONS: Set[str] = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp", ".gif"
}


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
        Validate that the given file represents a readable image supported by Pillow.

        Args:
            file_chunk_bytes: Binary contents of the file being validated.
            file_path: Path of the file being validated.

        Returns:
            bool: True if the file is a readable image, False otherwise.
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

        Args:
            file_bytes: Binary contents of the file being parsed.
            file_path: Path of the file being parsed.

        Returns:
            str: Full text content extracted from the image.
        """
        try:
            reader = cls._get_reader()
            results = reader.readtext(bytes(file_bytes), detail=0)
            return " ".join(results).strip()

        except Exception as e:
            return f"[OCR Error in {file_path.name}]: {str(e)}"


parser_cls: Type[Parser] = ImageParser
