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

    def test_known_text_extension_skips_magic(self):
        with patch("magic.from_buffer") as from_buffer:
            valid = TextParser.validate(b"test content", Path("test.txt"))

        self.assertTrue(valid)
        from_buffer.assert_not_called()

    def test_known_source_extension_skips_magic(self):
        with patch("mimetypes.guess_type", return_value=(None, None)):
            with patch("magic.from_buffer") as from_buffer:
                valid = TextParser.validate(b"class Example {}", Path("Example.java"))

        self.assertTrue(valid)
        from_buffer.assert_not_called()

    def test_known_repository_text_extensions_skip_magic(self):
        paths = [
            Path("locale/django.po"),
            Path("README.rst"),
            Path("template.py-tpl"),
            Path("icon.svg"),
            Path("shape.prj"),
            Path("MANIFEST.in"),
            Path("data.jsonl"),
            Path("template.tpl"),
            Path("sample.geojson"),
        ]

        for path in paths:
            with self.subTest(path=path):
                with patch("mimetypes.guess_type", return_value=(None, None)):
                    with patch("magic.from_buffer") as from_buffer:
                        valid = TextParser.validate(b"plain text content", path)

                self.assertTrue(valid)
                from_buffer.assert_not_called()

    def test_known_repository_text_filenames_skip_magic(self):
        paths = [
            Path("LICENSE"),
            Path("Makefile"),
            Path("Procfile"),
            Path("README"),
            Path(".gitkeep"),
            Path(".keep"),
            Path("django_bash_completion"),
            Path("spelling_wordlist"),
        ]

        for path in paths:
            with self.subTest(path=path):
                with patch("mimetypes.guess_type", return_value=(None, None)):
                    with patch("magic.from_buffer") as from_buffer:
                        valid = TextParser.validate(b"plain text content", path)

                self.assertTrue(valid)
                from_buffer.assert_not_called()

    def test_binary_validation_skips_magic(self):
        with patch("magic.from_buffer") as from_buffer:
            valid = TextParser.validate(b"binary\x00content", Path("test.bin"))

        self.assertFalse(valid)
        from_buffer.assert_not_called()

    def test_utf8_validation_skips_charset_detection(self):
        with patch("chardet.detect") as detect:
            valid = TextParser.validate("café".encode("utf-8"), Path("test.txt"))

        self.assertTrue(valid)
        detect.assert_not_called()

    def test_utf8_parse_skips_charset_detection(self):
        with patch("chardet.detect") as detect:
            content = TextParser.parse("café".encode("utf-8"), Path("test.txt"))

        self.assertEqual(content, "caf\u00e9")
        detect.assert_not_called()

    def test_non_utf8_text_validation_uses_charset_detection(self):
        with patch("chardet.detect", return_value={"encoding": "cp1252", "confidence": 0.73}) as detect:
            valid = TextParser.validate(b"caf\xe9", Path("test.txt"))

        self.assertTrue(valid)
        detect.assert_called_once()

    def test_non_utf8_text_parse_uses_charset_detection(self):
        with patch("chardet.detect", return_value={"encoding": "cp1252", "confidence": 0.73}) as detect:
            content = TextParser.parse(b"caf\xe9", Path("test.txt"))

        self.assertEqual(content, "café")
        detect.assert_called_once()

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
