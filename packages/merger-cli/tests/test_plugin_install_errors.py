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

def test_install_failure_with_details(tmp_path, mock_config_dir, capsys):
    # Create a broken Plugin that imports something non-existent
    broken_content = """
import non_existent_Plugin_foo_bar
from merger_plugin_api import Parser
EXTENSIONS = [".broken"]
class BrokenParser(Parser):
    @classmethod
    def validate(cls, file_bytes, file_path): return True
    @classmethod
    def parse(cls, file_bytes, file_path): return "broken"
parser_cls = BrokenParser
"""
    broken_path = tmp_path / "broken_parser.py"
    broken_path.write_text(broken_content)

    # Attempt to install it
    with patch.object(sys, 'argv', ['merger', '-i', str(broken_path)]):
        main()
    
    captured = capsys.readouterr()
    # Check if both errors are captured (Rich might print to stdout or stderr depending on setup)
    combined_output = captured.out + captured.err
    
    assert "Could not install plugin" in combined_output
    # Check for parts of the error message to avoid issues with wrapping/line breaks
    assert "ModuleNotFoundError" in combined_output
    assert "non_existent_Plugin_foo_bar" in combined_output
