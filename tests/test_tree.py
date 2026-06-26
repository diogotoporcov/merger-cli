from pathlib import Path
from unittest.mock import patch

import pytest
from merger.file_tree.scanner import FileTreeScanner
from merger.models import FileEntry, DirectoryEntry


@pytest.fixture
def sample_project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text("def add(a, b): return a + b", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Project", encoding="utf-8")
    (tmp_path / "ignore_me.log").write_text("log data", encoding="utf-8")
    return tmp_path

def test_tree_building(sample_project):
    tree = FileTreeScanner.scan(sample_project)
    
    assert isinstance(tree.root, DirectoryEntry)
    assert Path("src") in tree.root.children
    assert Path("README.md") in tree.root.children
    
    src_dir = tree.root.children[Path("src")]
    assert isinstance(src_dir, DirectoryEntry)
    assert Path("src/main.py") in src_dir.children

def test_tree_with_ignore(sample_project):
    tree = FileTreeScanner.scan(sample_project, ignore_patterns=["*.log"])
    
    assert Path("ignore_me.log") not in tree.root.children
    assert Path("README.md") in tree.root.children

def test_tree_merge(sample_project):
    tree = FileTreeScanner.scan(sample_project)
    
    def check_entry(entry):
        if isinstance(entry, FileEntry):
            assert entry.content is not None
        elif isinstance(entry, DirectoryEntry):
            for child in entry.children.values():
                check_entry(child)
    
    check_entry(tree.root)
    
    src_dir = tree.root.children[Path("src")]
    assert isinstance(src_dir, DirectoryEntry)
    main_py = src_dir.children[Path("src/main.py")]
    assert isinstance(main_py, FileEntry)
    assert main_py.content == "print('hello')"

def test_tree_sorting(tmp_path):
    (tmp_path / "Z_dir").mkdir()
    (tmp_path / "a_dir").mkdir()
    (tmp_path / "B_file.txt").touch()
    (tmp_path / "a_file.txt").touch()
    
    tree = FileTreeScanner.scan(tmp_path)
    children = [
        entry
        for entry in tree.root.children.values()
        if isinstance(entry, (DirectoryEntry, FileEntry))
    ]
    children_names = [entry.name for entry in children]
    
    # Expected: directories first, then alphabetical (case-insensitive)
    # a_dir, Z_dir, a_file.txt, B_file.txt
    assert children_names == ["a_dir", "Z_dir", "a_file.txt", "B_file.txt"]

def test_tree_nested_ignore(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").touch()
    (tmp_path / "src" / "utils.py").touch()
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").touch()
    
    # Ignore everything in tests directory
    tree = FileTreeScanner.scan(tmp_path, ignore_patterns=["tests/"])
    assert Path("src") in tree.root.children
    assert Path("tests") not in tree.root.children
    
    # Ignore specific nested file
    tree2 = FileTreeScanner.scan(tmp_path, ignore_patterns=["src/utils.py"])
    src_dir = tree2.root.children[Path("src")]
    assert isinstance(src_dir, DirectoryEntry)
    assert Path("src/main.py") in src_dir.children
    assert Path("src/utils.py") not in src_dir.children

def test_tree_double_wildcard_ignore(tmp_path):
    (tmp_path / "a" / "b" / "c").mkdir(parents=True)
    (tmp_path / "a" / "b" / "c" / "test.txt").touch()
    (tmp_path / "a" / "x.txt").touch()
    
    tree = FileTreeScanner.scan(tmp_path, ignore_patterns=["**/c/"])
    a_dir = tree.root.children[Path("a")]
    assert isinstance(a_dir, DirectoryEntry)
    b_dir = a_dir.children[Path("a/b")]
    assert isinstance(b_dir, DirectoryEntry)
    assert Path("a/b/c") not in b_dir.children
    assert Path("a/x.txt") in a_dir.children

def test_tree_empty(tmp_path):
    tree = FileTreeScanner.scan(tmp_path)
    assert len(tree.root.children) == 0


def test_scanner_reuses_validation_bytes_for_small_file(tmp_path):
    path = tmp_path / "small.txt"
    path.write_text("small file", encoding="utf-8")

    original_open = Path.open
    open_calls = []

    def open_path(open_path, *args, **kwargs):
        if open_path == path:
            open_calls.append(args)

        return original_open(open_path, *args, **kwargs)

    with patch.object(Path, "open", open_path):
        tree = FileTreeScanner.scan(tmp_path)

    entry = tree.root.children[Path("small.txt")]
    assert isinstance(entry, FileEntry)
    assert entry.content == "small file"
    assert open_calls == [("rb",)]


def test_scanner_reads_full_content_after_partial_validation_read(tmp_path):
    path = tmp_path / "large.txt"
    path.write_text("a" * 2048, encoding="utf-8")

    original_open = Path.open
    open_calls = []

    def open_path(open_path, *args, **kwargs):
        if open_path == path:
            open_calls.append(args)

        return original_open(open_path, *args, **kwargs)

    with patch.object(Path, "open", open_path):
        tree = FileTreeScanner.scan(tmp_path)

    entry = tree.root.children[Path("large.txt")]
    assert isinstance(entry, FileEntry)
    assert entry.content == "a" * 2048
    assert open_calls == [("rb",)]


def test_scanner_can_skip_file_content(tmp_path):
    path = tmp_path / "file.txt"
    path.write_text("content", encoding="utf-8")

    with patch.object(Path, "open", side_effect=AssertionError("file content should not be read")):
        tree = FileTreeScanner.scan(tmp_path, include_content=False)

    entry = tree.root.children[Path("file.txt")]
    assert isinstance(entry, FileEntry)
    assert entry.content is None


def test_scanner_reuses_sorted_child_directory_state(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "file.txt").write_text("content", encoding="utf-8")

    original_is_dir = Path.is_dir
    calls = []

    def is_dir(path):
        calls.append(path)
        return original_is_dir(path)

    with patch.object(Path, "is_dir", is_dir):
        FileTreeScanner.scan(tmp_path, include_content=False)

    assert calls.count(tmp_path / "src") == 1
    assert calls.count(tmp_path / "file.txt") == 1
