import sys
from unittest.mock import patch

import pytest
from merger.cli import main


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger.utils.config.get_merger_dir", lambda: tmp_path)
    # Clear the lazy DB cache in the managers
    from merger.parsing.registry import _manager as pm
    from merger.exporters.registry import _manager as em
    pm._db = None
    em._db = None
    return tmp_path

def test_install_failure_with_details(tmp_path, mock_config_dir, capsys):
    parser_content = """
import non_existent_Plugin_foo_bar
from merger.parsing.base import Parser
class BrokenParser(Parser):
    EXTENSIONS = [".broken"]
    @classmethod
    def validate(cls, file_bytes, file_path): return True
    @classmethod
    def parse(cls, file_bytes, file_path): return "broken"
"""
    parser_path = tmp_path / "broken_parser.py"
    parser_path.write_text(parser_content)

    with patch.object(sys, 'argv', ['merger', '-i', str(parser_path)]):
        main()
    
    captured = capsys.readouterr()
    # Check if both errors are captured (Rich might print to stdout or stderr).
    combined_output = captured.out + captured.err
    
    assert "Could not install plugin" in combined_output
    assert "ModuleNotFoundError" in combined_output
    assert "non_existent_Plugin_foo_bar" in combined_output
