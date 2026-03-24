import pytest
from pathlib import Path
from merger.utils.patterns import matches_pattern

@pytest.fixture
def root(tmp_path):
    return tmp_path

def test_literal_match(root):
    file_path = root / "README.md"
    file_path.touch()
    assert matches_pattern(file_path, root, "README.md")
    assert not matches_pattern(file_path, root, "other.md")

def test_directory_match(root):
    dir_path = root / "src"
    dir_path.mkdir()
    assert matches_pattern(dir_path, root, "src")
    assert matches_pattern(dir_path, root, "src/")
    assert not matches_pattern(dir_path, root, "src:")

def test_wildcard_one_segment(root):
    file_path = root / "src" / "main.py"
    file_path.parent.mkdir()
    file_path.touch()
    assert matches_pattern(file_path, root, "src/*.py")
    assert matches_pattern(file_path, root, "*/main.py")
    assert not matches_pattern(file_path, root, "src/*.js")

def test_double_wildcard(root):
    file_path = root / "src" / "utils" / "helper.py"
    file_path.parent.mkdir(parents=True)
    file_path.touch()
    assert matches_pattern(file_path, root, "src/**/*.py")
    assert matches_pattern(file_path, root, "**/*.py")
    assert matches_pattern(file_path, root, "src/**")
    assert not matches_pattern(file_path, root, "src/*.py")

def test_anchoring(root):
    file_path = root / "project" / "src" / "main.py"
    file_path.parent.mkdir(parents=True)
    file_path.touch()
    
    # Not anchored
    assert matches_pattern(file_path, root, "src/main.py")
    
    # Anchored to root
    assert not matches_pattern(file_path, root, "/src/main.py")
    assert matches_pattern(file_path, root, "/project/src/main.py")
    
    # Anchored to here (./)
    assert not matches_pattern(file_path, root, "./src/main.py")
    assert matches_pattern(file_path, root, "./project/src/main.py")

def test_type_qualifiers(root, monkeypatch):
    dir_path = root / "data"
    # dir_path.mkdir() # Skip actual creation to avoid some issues
    file_path = root / "config"
    # file_path.touch()

    def mock_is_dir(self):
        return self.name == "data"
    
    monkeypatch.setattr(Path, "is_dir", mock_is_dir)
    
    assert matches_pattern(dir_path, root, "data/")
    assert not matches_pattern(dir_path, root, "data:")
    
    assert matches_pattern(file_path, root, "config:")
    assert not matches_pattern(file_path, root, "config/")

def test_escape_suffix(root, monkeypatch):
    # Testing trailing !
    # Avoid actual file creation with illegal characters on Windows
    dir_path = root / "data:"

    def mock_is_dir(self):
        return ":" in self.name
    
    monkeypatch.setattr(Path, "is_dir", mock_is_dir)

    assert matches_pattern(dir_path, root, "data:!")

def test_embedded_wildcard(root):
    file_path = root / "log_2023_01_01.txt"
    file_path.touch()
    assert matches_pattern(file_path, root, "log_*.txt")
    assert matches_pattern(file_path, root, "*_2023_*.txt")
    assert not matches_pattern(file_path, root, "log_*.log")

def test_path_not_under_root(root):
    other_root = root.parent / "other"
    other_root.mkdir()
    file_path = other_root / "file.txt"
    file_path.touch()
    assert not matches_pattern(file_path, root, "file.txt")

def test_complex_double_wildcard(root):
    # Match any file in any sub-sub-directory
    (root / "a" / "b" / "c").mkdir(parents=True)
    (root / "a" / "b" / "c" / "test.py").touch()
    assert matches_pattern(root / "a" / "b" / "c" / "test.py", root, "a/**/test.py")
    assert matches_pattern(root / "a" / "b" / "c" / "test.py", root, "**/b/**")
    assert matches_pattern(root / "a" / "b" / "c" / "test.py", root, "**/*.py")
    assert matches_pattern(root / "a" / "b" / "c", root, "a/**/c")

def test_empty_pattern(root):
    (root / "file.txt").touch()
    # If pattern is empty, it shouldn't match anything unless we are checking the root itself?
    # Actually, pattern "" split by "/" results in () if we handle it specifically.
    # Let's see how matches_pattern handles it.
    assert not matches_pattern(root / "file.txt", root, "")
    # Does it match the root itself?
    assert matches_pattern(root, root, "")

def test_trailing_slashes_and_colons(root):
    (root / "dir").mkdir()
    (root / "file").touch()
    
    assert matches_pattern(root / "dir", root, "dir/")
    assert not matches_pattern(root / "dir", root, "dir:")
    assert matches_pattern(root / "file", root, "file:")
    assert not matches_pattern(root / "file", root, "file/")
    
    # With escape suffix
    assert not matches_pattern(root / "dir", root, "dir/!") # should look for literal "dir/"
    # Note: creating a file named "dir/" is not possible on many systems, but we can test logic

def test_dots_in_path(root):
    (root / "src" / "main.py").mkdir(parents=True, exist_ok=True)
    file_path = root / "src" / "main.py"
    file_path.touch()
    
    assert matches_pattern(file_path, root, "./src/main.py")
    assert matches_pattern(file_path, root, "src/./main.py") # if it's not anchored, it might fail because of how split works
    # Wait, "src/./main.py".split("/") is ("src", ".", "main.py")
    # Our matches_pattern implementation doesn't handle "." or ".." in patterns specially unless it's leading "./"

def test_multiple_wildcards_in_segment(root):
    (root / "foobar.txt").touch()
    assert matches_pattern(root / "foobar.txt", root, "f*b*.txt")
    assert matches_pattern(root / "foobar.txt", root, "*oo*ar*")
    assert not matches_pattern(root / "foobar.txt", root, "*oo*az*")
