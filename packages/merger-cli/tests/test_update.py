
import unittest
from merger_cli.utils.update import is_newer_version

class TestUpdate(unittest.TestCase):
    def test_is_newer_version(self):
        self.assertTrue(is_newer_version("1.10.0", "1.9.0"))
        self.assertTrue(is_newer_version("2.0.0", "1.9.9"))
        self.assertFalse(is_newer_version("1.9.0", "1.10.0"))
        self.assertFalse(is_newer_version("1.1.0", "1.1.0"))
        
        # Test edge cases for version comparison.
        self.assertTrue(is_newer_version("1.1.0", "1.1.0a1"))
        self.assertTrue(is_newer_version("1.1.0b1", "1.1.0a1"))
        self.assertTrue(is_newer_version("1.1.0rc1", "1.1.0b2"))
        self.assertTrue(is_newer_version("1.1.0", "1.1.0rc1"))
        self.assertTrue(is_newer_version("1.1.0.post1", "1.1.0"))
        self.assertFalse(is_newer_version("1.1.0a1", "1.1.0"))

if __name__ == "__main__":
    unittest.main()
