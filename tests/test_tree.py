import pytest
from pathlib import Path
from merger.file_tree.tree import FileTree
from merger.file_tree.entries import FileEntry, DirectoryEntry

@pytest.fixture
def sample_project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text("def add(a, b): return a + b", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Project", encoding="utf-8")
    (tmp_path / "ignore_me.log").write_text("log data", encoding="utf-8")
    return tmp_path

def test_tree_building(sample_project):
    tree = FileTree.from_path(sample_project)
    
    assert isinstance(tree.root, DirectoryEntry)
    assert Path("src") in tree.root.children
    assert Path("README.md") in tree.root.children
    
    src_dir = tree.root.children[Path("src")]
    assert isinstance(src_dir, DirectoryEntry)
    assert Path("src/main.py") in src_dir.children

def test_tree_with_ignore(sample_project):
    tree = FileTree.from_path(sample_project, ignore_patterns=["*.log"])
    
    assert Path("ignore_me.log") not in tree.root.children
    assert Path("README.md") in tree.root.children

def test_tree_merge(sample_project):
    tree = FileTree.from_path(sample_project)
    
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
    
    tree = FileTree.from_path(tmp_path)
    children_names = [p.name for p in tree.root.children.values()]
    
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
    tree = FileTree.from_path(tmp_path, ignore_patterns=["tests/"])
    assert Path("src") in tree.root.children
    assert Path("tests") not in tree.root.children
    
    # Ignore specific nested file
    tree2 = FileTree.from_path(tmp_path, ignore_patterns=["src/utils.py"])
    src_dir = tree2.root.children[Path("src")]
    assert Path("src/main.py") in src_dir.children
    assert Path("src/utils.py") not in src_dir.children

def test_tree_double_wildcard_ignore(tmp_path):
    (tmp_path / "a" / "b" / "c").mkdir(parents=True)
    (tmp_path / "a" / "b" / "c" / "test.txt").touch()
    (tmp_path / "a" / "x.txt").touch()
    
    tree = FileTree.from_path(tmp_path, ignore_patterns=["**/c/"])
    a_dir = tree.root.children[Path("a")]
    b_dir = a_dir.children[Path("a/b")]
    assert Path("a/b/c") not in b_dir.children
    assert Path("a/x.txt") in a_dir.children

def test_tree_empty(tmp_path):
    tree = FileTree.from_path(tmp_path)
    assert len(tree.root.children) == 0
