import sys
from unittest.mock import patch

import pytest
from merger.cli import main


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger.utils.config.get_merger_dir", lambda: tmp_path)
    return tmp_path

def test_unified_module_system(tmp_path, mock_config_dir, capsys):
    # 1. Create a mock parser module
    parser_content = """
from merger.parsing.parser import Parser
class MockParser(Parser):
    EXTENSIONS = [".mock"]
    @classmethod
    def validate(cls, file_bytes, **kwargs): return True
    @classmethod
    def parse(cls, file_bytes, **kwargs): return "mocked"
parser_cls = MockParser
"""
    parser_path = tmp_path / "mock_parser.py"
    parser_path.write_text(parser_content)

    # 2. Create a mock exporter module
    exporter_content = """
from merger.exporters.tree_exporter import TreeExporter
class MockExporter(TreeExporter):
    NAME = "MOCK"
    FILE_EXTENSION = ".mock"
    @classmethod
    def export(cls, tree): return b"mocked export"
exporter_cls = MockExporter
"""
    exporter_path = tmp_path / "mock_exporter.py"
    exporter_path.write_text(exporter_content)

    # 3. Install parser using unified -i
    with patch.object(sys, 'argv', ['merger', '-i', str(parser_path)]):
        main()
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "Parser module" in combined and "installed successfully" in combined

    # 4. Install exporter using unified -i
    with patch.object(sys, 'argv', ['merger', '-i', str(exporter_path)]):
        main()
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "Exporter module" in combined and "installed successfully" in combined

    # 5. List modules using unified -l
    with patch.object(sys, 'argv', ['merger', '-l']):
        main()
    captured = capsys.readouterr()
    assert "Installed Parser Modules" in captured.out
    assert "Installed Exporter Modules" in captured.out
    assert "mock_parser.py" in captured.out
    assert "mock_exporter.py" in captured.out

    # 6. Uninstall parser using unified -u
    # We need to find the ID. ModuleManager uses hash of file.
    # But since we only have one, we can just check if "mock_parser.py" disappeared from list.
    from merger.parsing.registry import list_parsers
    parsers = list_parsers()
    parser_id = list(parsers.keys())[0]

    with patch.object(sys, 'argv', ['merger', '-u', parser_id]):
        main()
    captured = capsys.readouterr()
    assert f"Parser module '{parser_id}' uninstalled" in captured.err or f"Parser module '{parser_id}' uninstalled" in captured.out

    # 7. List again to verify
    with patch.object(sys, 'argv', ['merger', '-l']):
        main()
    captured = capsys.readouterr()
    assert "Installed Parser Modules" not in captured.out or "mock_parser.py" not in captured.out
    assert "Installed Exporter Modules" in captured.out
    assert "mock_exporter.py" in captured.out

    # 8. Uninstall all
    with patch.object(sys, 'argv', ['merger', '-u', '*']):
        main()
    captured = capsys.readouterr()
    assert "All modules uninstalled" in captured.err or "All modules uninstalled" in captured.out

    with patch.object(sys, 'argv', ['merger', '-l']):
        main()
    captured = capsys.readouterr()
    assert "No custom modules installed" in captured.err or "No custom modules installed" in captured.out
