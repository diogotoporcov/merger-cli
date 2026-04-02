import sys
from unittest.mock import patch

import pytest
from merger_cli.cli import main


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger_cli.utils.config.get_merger_dir", lambda: tmp_path)
    # Clear the lazy DB cache in the managers
    from merger_cli.parsing.registry import _manager as pm
    from merger_cli.exporters.registry import _manager as em
    pm._db = None
    em._db = None
    return tmp_path

def test_unified_Plugin_system(tmp_path, mock_config_dir, capsys):
    # 1. Create a mock Parser plugin
    parser_content = """
from merger_plugin_api import Parser
EXTENSIONS = [".mock"]
class MockParser(Parser):
    @classmethod
    def validate(cls, file_bytes, file_path): return True
    @classmethod
    def parse(cls, file_bytes, file_path): return "mocked"
parser_cls = MockParser
"""
    parser_path = tmp_path / "mock_parser.py"
    parser_path.write_text(parser_content)

    # 2. Create a mock Exporter plugin
    exporter_content = """
from merger_plugin_api import TreeExporter
NAME = "MOCK"
FILE_EXTENSION = ".mock"
class MockExporter(TreeExporter):
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
    assert "Parser plugin" in combined and "installed successfully" in combined

    # 4. Install exporter using unified -i
    with patch.object(sys, 'argv', ['merger', '-i', str(exporter_path)]):
        main()
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "Exporter plugin" in combined and "installed successfully" in combined

    # 5. List Plugins using unified -l
    with patch.object(sys, 'argv', ['merger', '-l']):
        main()
    captured = capsys.readouterr()
    assert "Installed Parser plugins" in captured.out
    assert "Installed Exporter plugins" in captured.out
    assert "mock_parser.py" in captured.out
    assert "mock_exporter.py" in captured.out

    # 6. Uninstall parser using unified -u
    # The ID must be found using list_parsers().
    from merger_cli.parsing.registry import list_parsers
    parsers = list_parsers()
    parser_id = parsers[0].id

    with patch.object(sys, 'argv', ['merger', '-u', parser_id]):
        main()
    captured = capsys.readouterr()
    assert f"Parser plugin '{parser_id}' uninstalled" in captured.err or f"Parser plugin '{parser_id}' uninstalled" in captured.out

    # 7. List again to verify
    with patch.object(sys, 'argv', ['merger', '-l']):
        main()
    captured = capsys.readouterr()
    assert "Installed Parser plugins" not in captured.out or "mock_parser.py" not in captured.out
    assert "Installed Exporter plugins" in captured.out
    assert "mock_exporter.py" in captured.out

    # 8. Uninstall all (cancelled)
    with patch("rich.prompt.Confirm.ask", return_value=False), \
         patch.object(sys, 'argv', ['merger', '-u', '*']):
        main()
    captured = capsys.readouterr()
    assert "Uninstallation cancelled" in captured.out or "Uninstallation cancelled" in captured.err

    # 9. Uninstall all (confirmed)
    with patch("rich.prompt.Confirm.ask", return_value=True), \
         patch.object(sys, 'argv', ['merger', '-u', '*']):
        main()
    captured = capsys.readouterr()
    assert "All plugins uninstalled" in captured.err or "All plugins uninstalled" in captured.out

    with patch.object(sys, 'argv', ['merger', '-l']):
        main()
    captured = capsys.readouterr()
    assert "No custom plugins installed" in captured.err or "No custom plugins installed" in captured.out
