import unittest
from pathlib import Path
from unittest.mock import patch

from merger_cli.parsing.impl.default_parser import DefaultParser
from merger_cli.utils.magic import check_libmagic_availability


class TestMagicUtils(unittest.TestCase):
    def test_magic_missing_error(self):
        with patch("magic.from_buffer", side_effect=OSError("failed to find libmagic")):
            with self.assertRaises(RuntimeError) as cm:
                DefaultParser.guess_mime_type(b"test content", Path("test.txt"))
            
            error_msg = str(cm.exception)
            self.assertIn("libmagic is required but not found", error_msg)
            # Check for platform-specific tip (assuming it's Windows, Linux or macOS)
            self.assertTrue(any(word in error_msg for word in ["pip", "apt-get", "brew", "dnf", "pacman"]))

    def test_check_libmagic_availability_success(self):
        with patch("magic.from_buffer", return_value="text/plain"):
            check_libmagic_availability()

    def test_check_libmagic_availability_failure(self):
        with patch("magic.from_buffer", side_effect=ImportError("libmagic not found")):
            with self.assertRaises(RuntimeError) as cm:
                check_libmagic_availability()
            self.assertIn("libmagic is required", str(cm.exception))

    def test_unexpected_magic_error(self):
        with patch("magic.from_buffer", side_effect=Exception("something went wrong")):
            with self.assertRaises(RuntimeError) as cm:
                DefaultParser.guess_mime_type(b"test content", Path("test.txt"))
            
            error_msg = str(cm.exception)
            self.assertIn("Error while identifying file type with libmagic: something went wrong", error_msg)

    def test_octet_stream_fallback(self):
        # If magic returns application/octet-stream, a fallback to mimetypes guess is used
        with patch("magic.from_buffer", return_value="application/octet-stream"):
            with patch("mimetypes.guess_type", return_value=("text/plain", None)):
                mime = DefaultParser.guess_mime_type(b"test content", Path("test.txt"))
                self.assertEqual(mime, "text/plain")

if __name__ == "__main__":
    unittest.main()
