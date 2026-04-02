import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

from merger_cli.cli.utils import handle_update, handle_update_injected
from merger_cli.utils.config import get_or_create_site_packages_dir

@pytest.fixture
def mock_merger_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger_cli.utils.config.get_merger_dir", lambda: tmp_path)
    return tmp_path

@patch("merger_cli.cli.utils.logger.info")
def test_handle_update_pip(mock_logger_info, mock_merger_dir):
    # Ensure sys.frozen is False
    if hasattr(sys, "frozen"):
        delattr(sys, "frozen")
    
    with patch("os.environ", {}):
        handle_update()
        
        messages = [call.args[0] for call in mock_logger_info.call_args_list]
        assert any("distributed via standalone installers" in msg for msg in messages)

@patch("merger_cli.cli.utils.logger.info")
def test_handle_update_frozen(mock_logger_info, mock_merger_dir):
    with patch("sys.frozen", True, create=True):
        handle_update()
        
        messages = [call.args[0] for call in mock_logger_info.call_args_list]
        assert any("standalone binary" in msg for msg in messages)

@patch("merger_cli.cli.utils.logger.info")
def test_handle_update_pipx(mock_logger_info, mock_merger_dir):
    if hasattr(sys, "frozen"):
        delattr(sys, "frozen")
        
    with patch("os.environ", {"PIPX_BIN_DIR": "/path/to/pipx"}):
        handle_update()
        
        messages = [call.args[0] for call in mock_logger_info.call_args_list]
        assert any("distributed via standalone installers" in msg for msg in messages)

@patch("merger_cli.cli.utils.handle_inject")
@patch("importlib.metadata.distributions")
def test_handle_update_injected_metadata(mock_distributions, mock_handle_inject, mock_merger_dir):
    site_packages = get_or_create_site_packages_dir()
    site_packages.mkdir(parents=True, exist_ok=True)
    (site_packages / "dummy").touch()
    
    mock_dist = MagicMock()
    mock_dist.name = "package1"
    mock_distributions.return_value = [mock_dist]
    
    handle_update_injected()
    
    mock_handle_inject.assert_called_once_with(packages=["package1"])

@patch("merger_cli.cli.utils.handle_inject")
def test_handle_update_injected_fallback(mock_handle_inject, mock_merger_dir):
    site_packages = get_or_create_site_packages_dir()
    site_packages.mkdir(parents=True, exist_ok=True)
    (site_packages / "package2-2.0.dist-info").mkdir()
    
    with patch("importlib.metadata.distributions", side_effect=Exception("metadata fail")):
        handle_update_injected()
    
    mock_handle_inject.assert_called_once_with(packages=["package2"])

def test_handle_update_injected_none(mock_merger_dir, caplog):
    site_packages = get_or_create_site_packages_dir()
    if site_packages.exists():
        import shutil
        shutil.rmtree(site_packages)
    
    handle_update_injected()
    assert "No injected packages found to update" in caplog.text
