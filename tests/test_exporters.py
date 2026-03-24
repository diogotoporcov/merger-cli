import json
import pytest
from pathlib import Path
from merger.file_tree.tree import FileTree
from merger.exporters.impl.plain_text_exporter import PlainTextExporter
from merger.exporters.impl.directory_tree_exporter import DirectoryTreeExporter
from merger.exporters.impl.json_exporter import JsonExporter
from merger.exporters.impl.json_tree_exporter import JsonTreeExporter
from merger.exporters.impl.tree_with_plain_text_exporter import TreeWithPlainTextExporter

@pytest.fixture
def complex_tree(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Project", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "info.txt").write_text("some data", encoding="utf-8")
    # FileTree.from_path will use the default parser and merger.ignore if it existed
    # but we can pass an empty list for ignore_patterns
    return FileTree.from_path(tmp_path, ignore_patterns=[])

def test_plain_text_exporter(complex_tree):
    output = PlainTextExporter.export(complex_tree).decode()
    assert "<<FILE_START: ./README.md>>" in output
    assert "# Project" in output
    assert "<<FILE_END: ./README.md>>" in output
    assert "<<FILE_START: ./src/main.py>>" in output
    assert "print('hello')" in output

def test_directory_tree_exporter(complex_tree):
    output = DirectoryTreeExporter.export(complex_tree).decode()
    # Current root name might be the tmp_path name
    assert "src/" in output
    assert "├── data/" in output or "└── data/" in output
    assert "├── README.md" in output or "└── README.md" in output
    assert "│   └── main.py" in output or "    └── main.py" in output

def test_json_exporter(complex_tree):
    output = JsonExporter.export(complex_tree).decode()
    data = json.loads(output)
    # JsonExporter produces a Dict[str, str] (path to content)
    assert isinstance(data, dict)
    assert "./README.md" in data
    assert "./src/main.py" in data
    assert data["./src/main.py"] == "print('hello')"

def test_json_tree_exporter(complex_tree):
    output = JsonTreeExporter.export(complex_tree).decode()
    data = json.loads(output)
    assert data["path"] == "."
    assert "src" in data["children"]
    assert "README.md" in data["children"]
    assert data["children"]["src"]["type"] == "directory"

def test_tree_with_plain_text_exporter(complex_tree):
    output = TreeWithPlainTextExporter.export(complex_tree).decode()
    assert "src/" in output
    assert "<<FILE_START: ./src/main.py>>" in output

def test_directory_tree_exporter_order(tmp_path):
    (tmp_path / "z_dir").mkdir()
    (tmp_path / "a_dir").mkdir()
    (tmp_path / "b_file.txt").touch()
    (tmp_path / "a_file.txt").touch()
    
    tree = FileTree.from_path(tmp_path, ignore_patterns=[])
    output = DirectoryTreeExporter.export(tree).decode()
    
    lines = [line for line in output.splitlines() if line]
    # lines[0] is root (tmp_path name)
    # then a_dir/, z_dir/, a_file.txt, b_file.txt
    assert "a_dir/" in lines[1]
    assert "z_dir/" in lines[2]
    assert "a_file.txt" in lines[3]
    assert "b_file.txt" in lines[4]
