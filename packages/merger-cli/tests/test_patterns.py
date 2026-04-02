import pytest
import platform
from merger_cli.utils.patterns import matches_pattern

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
    
    # In standard Git rules, a pattern with an internal slash is anchored to the root.
    # So "src/main.py" does NOT match "project/src/main.py"
    assert not matches_pattern(file_path, root, "src/main.py")
    
    # Recursive match requires **
    assert matches_pattern(file_path, root, "**/src/main.py")
    
    # Anchored to root explicitly
    assert not matches_pattern(file_path, root, "/src/main.py")
    assert matches_pattern(file_path, root, "/project/src/main.py")
    
    # Anchored to here (./) - normalized to /
    assert not matches_pattern(file_path, root, "./src/main.py")
    assert matches_pattern(file_path, root, "./project/src/main.py")

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

def test_dots_in_path(root):
    (root / "src" / "main.py").mkdir(parents=True, exist_ok=True)
    file_path = root / "src" / "main.py"
    file_path.touch()
    
    # Normalized by compile_patterns
    assert matches_pattern(file_path, root, "./src/main.py")

def test_multiple_wildcards_in_segment(root):
    (root / "foobar.txt").touch()
    assert matches_pattern(root / "foobar.txt", root, "f*b*.txt")
    assert matches_pattern(root / "foobar.txt", root, "*oo*ar*")
    assert not matches_pattern(root / "foobar.txt", root, "*oo*az*")

def test_empty_pattern(root):
    (root / "file.txt").touch()
    # Empty pattern only matches root.
    assert not matches_pattern(root / "file.txt", root, "")
    assert matches_pattern(root, root, "")

def test_type_qualifiers(root):
    # Setup files and directories
    (root / "data").mkdir()
    (root / "data" / "sub").mkdir()
    (root / "data.txt").touch()
    (root / "readme_file").touch()
    (root / "README_DIR").mkdir()
    if platform.system() != "Windows":
        (root / "data_file_colon").touch()
        (root / "data_dir_colon").mkdir(exist_ok=True)

    # / suffix - directory only
    assert matches_pattern(root / "data", root, "data/")
    assert not matches_pattern(root / "data.txt", root, "data/")
    
    # : suffix - file only
    assert matches_pattern(root / "data.txt", root, "data.txt:")
    assert not matches_pattern(root / "data", root, "data:")
    
    # ! suffix - literal (escapes : and /)
    # data_file_colon! matches both file and directory named data_file_colon
    if platform.system() != "Windows":
        file_colon = root / "data_file_colon"
        assert matches_pattern(file_colon, root, "data_file_colon!")
    
    # Verify standard behavior matches both files and directories.
    assert matches_pattern(root / "readme_file", root, "readme_file")
    assert matches_pattern(root / "README_DIR", root, "README_DIR")

def test_complex_qualifiers(root):
    (root / "src").mkdir()
    (root / "src" / "main.py").touch()
    (root / "src" / "utils").mkdir()
    
    # Match all files in src
    assert matches_pattern(root / "src" / "main.py", root, "src/*:")
    assert not matches_pattern(root / "src" / "utils", root, "src/*:")
    
    # Match all directories in src
    assert matches_pattern(root / "src" / "utils", root, "src/*/")
    assert not matches_pattern(root / "src" / "main.py", root, "src/*/")

@pytest.mark.skipif(platform.system() == "Windows", reason="Colon not allowed in filenames on Windows")
def test_literal_escapes(root):
    # data_file:! -> matches literal "data_file:" (either file or dir)
    (root / "data_file:").touch()
    assert matches_pattern(root / "data_file:", root, "data_file:!")
    
    # data_file:: -> matches literal "data_file:" (file only)
    assert matches_pattern(root / "data_file:", root, "data_file::")
    (root / "dir:").mkdir()
    assert not matches_pattern(root / "dir:", root, "dir::")
    
    # data_dir:/ -> matches literal "data_dir:" (directory only)
    (root / "data_dir:").mkdir()
    assert matches_pattern(root / "data_dir:", root, "data_dir:/")
    (root / "file:").touch()
    assert not matches_pattern(root / "file:", root, "file:/")
    
    # data!! -> matches literal "data!" (either file or dir)
    (root / "data!").touch()
    assert matches_pattern(root / "data!", root, "data!!")
    
    # data!/ -> matches literal "data!" (directory only)
    (root / "dir!").mkdir()
    assert matches_pattern(root / "dir!", root, "dir!/")
    
    # data!: -> matches literal "data!" (file only)
    (root / "file!").touch()
    assert matches_pattern(root / "file!", root, "file!:")
