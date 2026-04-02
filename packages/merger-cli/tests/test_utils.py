import pytest
from pathlib import Path
from merger_cli.utils.ignore_templates import list_ignore_templates, read_ignore_template
from merger_cli.exceptions import UnknownIgnoreTemplate

def test_list_ignore_templates():
    templates = list_ignore_templates()
    assert isinstance(templates, list)
    assert "DEFAULT" in templates
    assert "PYTHON" in templates
    # Test that DEFAULT is first, then the rest is sorted
    assert templates[0] == "DEFAULT"
    assert templates[1:] == sorted(templates[1:])

def test_read_ignore_template():
    content = read_ignore_template("PYTHON")
    assert "__pycache__/" in content
    
    with pytest.raises(UnknownIgnoreTemplate):
        read_ignore_template("NON_EXISTENT")
from merger_cli.utils.files import read_file_bytes, read_merger_ignore_file
from merger_cli.utils.hash import hash_from_file

def test_read_file_bytes(tmp_path):
    file_path = tmp_path / "test.bin"
    content = b"\x00\x01\x02\x03\x04\x05"
    file_path.write_bytes(content)
    
    assert read_file_bytes(file_path) == content
    assert read_file_bytes(file_path, chunk_size=3) == b"\x00\x01\x02"

def test_read_merger_ignore_file(tmp_path):
    ignore_file = tmp_path / "merger.ignore"
    ignore_file.write_text("*.py\n\n  # comment\nsrc/\n  ", encoding="utf-8")
    
    patterns = read_merger_ignore_file(ignore_file)
    # The current implementation DOES NOT filter comments starting with #
    # and it might not filter leading/trailing whitespace properly if they are not just spaces
    # Let's check what it currently does.
    # line = line.strip()
    # if line: patterns.add(line)
    
    assert "*.py" in patterns
    assert "src/" in patterns
    assert "# comment" not in patterns
    assert "" not in patterns

def test_hash_from_file(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello world", encoding="utf-8")
    
    h1 = hash_from_file(file_path, length=8)
    assert len(h1) == 8
    
    h2 = hash_from_file(file_path, length=12)
    assert len(h2) == 12
    assert h2.startswith(h1)
    
    # Check different content
    file_path.write_text("hello world!", encoding="utf-8")
    h3 = hash_from_file(file_path, length=8)
    assert h1 != h3
