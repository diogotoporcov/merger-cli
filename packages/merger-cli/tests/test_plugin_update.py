import pytest
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
from merger_cli.cli import main
from merger_cli.utils.db import PluginRecord

@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger_cli.utils.config.get_merger_dir", lambda: tmp_path)
    # Clear lazy DB caches
    try:
        from merger_cli.parsing.registry import _manager as pm
        pm._db = None
    except ImportError:
        pass
    try:
        from merger_cli.exporters.registry import _manager as em
        em._db = None
    except ImportError:
        pass
    return tmp_path

def test_handle_plugin_update_no_plugins(capsys, mock_config_dir):
    with patch.object(sys, 'argv', ['merger', '--update-plugins']):
        with patch("merger_cli.cli.utils.Confirm.ask", return_value=False):
            main()

    captured = capsys.readouterr()
    all_out = captured.out + captured.err
    assert "No custom plugins installed to check for dependency updates." in all_out

def test_handle_plugin_update_with_plugins(tmp_path, monkeypatch, capsys, mock_config_dir):
    # Setup a dummy plugin in DB
    plugin_path = tmp_path / "my_plugin.py"
    plugin_path.write_text("REQUIREMENTS = ['pillow']\nclass MyParser: pass\nparser_cls = MyParser")
    
    from merger_cli.utils.db import DatabaseManager
    db = DatabaseManager()
    db.add_plugin(PluginRecord(
        id="abc",
        name="my_plugin",
        type="parser",
        path=str(plugin_path),
        original_name="my_plugin.py",
        extensions=[".test"]
    ))

    # Mock uv_install and Confirm.ask
    with patch("merger_cli.cli.utils.Confirm.ask", return_value=True) as mock_confirm:
        with patch("merger_cli.utils.uv.uv_install") as mock_uv:
            with patch.object(sys, 'argv', ['merger', '--update-plugins']):
                main()
    
    # Verify it tried to install plugin dependencies
    mock_uv.assert_any_call(['pillow'], target=mock_config_dir / "site-packages")
    # Verify it asked for core dependencies
    mock_confirm.assert_called_with("Do you wish to update core dependencies too?")
    # Verify it tried to install core dependencies
    mock_uv.assert_any_call(["pydantic", "rich", "pathspec", "packaging", "rich-argparse"], target=mock_config_dir / "site-packages")

def test_handle_plugin_update_yes_flag(tmp_path, monkeypatch, capsys, mock_config_dir):
    # Setup a dummy plugin in DB
    plugin_path = tmp_path / "my_plugin.py"
    plugin_path.write_text("REQUIREMENTS = ['pillow']\nclass MyParser: pass\nparser_cls = MyParser")
    
    from merger_cli.utils.db import DatabaseManager
    db = DatabaseManager()
    db.add_plugin(PluginRecord(
        id="abc",
        name="my_plugin",
        type="parser",
        path=str(plugin_path),
        original_name="my_plugin.py",
        extensions=[".test"]
    ))

    # Mock uv_install and Confirm.ask
    with patch("merger_cli.cli.utils.Confirm.ask") as mock_confirm:
        with patch("merger_cli.utils.uv.uv_install") as mock_uv:
            # Use -y flag to bypass confirmation
            with patch.object(sys, 'argv', ['merger', '--update-plugins', '-y']):
                main()
    
    # Confirm.ask should NOT be called because force=True (from -y)
    mock_confirm.assert_not_called()
    # But it should still update core dependencies
    mock_uv.assert_any_call(["pydantic", "rich", "pathspec", "packaging", "rich-argparse"], target=mock_config_dir / "site-packages")
