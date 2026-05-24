import unittest
from pathlib import Path
from unittest.mock import patch

import magic
from merger.parsing.impl.text import TextParser
from merger.utils.magic import check_libmagic_availability


class TestMagicUtils(unittest.TestCase):
    def test_magic_exception_fallback(self):
        # If magic raises MagicException, we should fallback to mimetypes
        with patch("magic.from_buffer", side_effect=magic.MagicException("regex error")):
            with patch("mimetypes.guess_type", return_value=("text/x-python", None)):
                mime = TextParser.guess_mime_type(b"class A: pass", Path("test.py"))
                self.assertEqual(mime, "text/x-python")

    def test_magic_missing_error_fallback(self):
        # Now it should NOT raise RuntimeError, but fallback to mimetypes
        with patch("magic.from_buffer", side_effect=OSError("failed to find libmagic")):
            with patch("mimetypes.guess_type", return_value=("text/plain", None)):
                mime = TextParser.guess_mime_type(b"test content", Path("test.txt"))
                self.assertEqual(mime, "text/plain")

    def test_check_libmagic_availability_success(self):
        with patch("magic.from_buffer", return_value="text/plain"):
            check_libmagic_availability()

    def test_check_libmagic_availability_failure(self):
        with patch("magic.from_buffer", side_effect=ImportError("libmagic not found")):
            with self.assertRaises(RuntimeError) as cm:
                check_libmagic_availability()
            self.assertIn("libmagic is required", str(cm.exception))

    def test_unexpected_magic_error_fallback(self):
        # Now it should NOT raise RuntimeError, but fallback to mimetypes
        with patch("magic.from_buffer", side_effect=Exception("something went wrong")):
            with patch("mimetypes.guess_type", return_value=("text/x-python", None)):
                mime = TextParser.guess_mime_type(b"test content", Path("test.py"))
                self.assertEqual(mime, "text/x-python")

    def test_octet_stream_fallback(self):
        # If magic returns application/octet-stream, a fallback to mimetypes guess is used
        with patch("magic.from_buffer", return_value="application/octet-stream"):
            with patch("mimetypes.guess_type", return_value=("text/plain", None)):
                mime = TextParser.guess_mime_type(b"test content", Path("test.txt"))
                self.assertEqual(mime, "text/plain")

    def test_final_fallback_to_text(self):
        # If both magic and mimetypes fail, but it looks like text
        with patch("magic.from_buffer", return_value=None):
            with patch("mimetypes.guess_type", return_value=(None, None)):
                # Content without null bytes and high non-printable ratio
                mime = TextParser.guess_mime_type(b"plain text content", Path("unknown_file"))
                self.assertEqual(mime, "text/plain")

    def test_final_fallback_to_binary(self):
        # If both magic and mimetypes fail, and it looks like binary
        with patch("magic.from_buffer", return_value=None):
            with patch("mimetypes.guess_type", return_value=(None, None)):
                # Content with null bytes
                mime = TextParser.guess_mime_type(b"binary\x00content", Path("unknown_file"))
                self.assertEqual(mime, "application/octet-stream")

if __name__ == "__main__":
    unittest.main()
