import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import shutil

from merger_cli.cli.utils import handle_inject, handle_purge_packages
from merger_cli.utils.config import get_or_create_site_packages_dir

@pytest.fixture
def mock_merger_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger_cli.utils.config.get_merger_dir", lambda: tmp_path)
    return tmp_path

def test_get_or_create_site_packages_dir(mock_merger_dir):
    path = get_or_create_site_packages_dir()
    assert path.exists()
    assert path.name == "site-packages"
    assert path.parent == mock_merger_dir

@patch("subprocess.check_call")
def test_handle_inject_packages(mock_check_call, mock_merger_dir):
    packages = ["pymupdf", "pydantic"]
    handle_inject(packages=packages)
    
    mock_check_call.assert_called_once()
    args = mock_check_call.call_args[0][0]
    assert sys.executable in args
    assert "-m" in args
    assert "pip" in args
    assert "install" in args
    assert "--target" in args
    assert str(get_or_create_site_packages_dir()) in args
    assert "pymupdf" in args
    assert "pydantic" in args
    assert "--no-input" in args

@patch("subprocess.check_call")
def test_handle_inject_requirements(mock_check_call, mock_merger_dir, tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("pymupdf\npydantic")
    
    handle_inject(requirements_file=req_file)
    
    mock_check_call.assert_called_once()
    args = mock_check_call.call_args[0][0]
    assert "-r" in args
    assert str(req_file) in args

@patch("subprocess.check_call")
def test_handle_inject_requirements_not_found(mock_check_call, mock_merger_dir, caplog):
    req_file = Path("non_existent_req.txt")
    handle_inject(requirements_file=req_file)
    
    mock_check_call.assert_not_called()
    assert "Requirements file not found" in caplog.text

@patch("merger_cli.cli.utils.Confirm.ask")
def test_handle_purge_packages(mock_confirm, mock_merger_dir):
    site_packages = get_or_create_site_packages_dir()
    site_packages.mkdir(parents=True, exist_ok=True)
    (site_packages / "some_package").mkdir()
    
    mock_confirm.return_value = True
    handle_purge_packages()
    
    assert site_packages.exists()
    assert not any(site_packages.iterdir())

@patch("merger_cli.cli.utils.Confirm.ask")
def test_handle_purge_packages_no_confirm(mock_confirm, mock_merger_dir):
    site_packages = get_or_create_site_packages_dir()
    site_packages.mkdir(parents=True, exist_ok=True)
    (site_packages / "some_package").mkdir()
    
    mock_confirm.return_value = False
    handle_purge_packages()
    
    assert any(site_packages.iterdir())

def test_handle_purge_packages_empty(mock_merger_dir, caplog):
    site_packages = get_or_create_site_packages_dir()
    if site_packages.exists():
        shutil.rmtree(site_packages)
    site_packages.mkdir(parents=True, exist_ok=True)
    
    handle_purge_packages()
    assert "No injected packages found to purge" in caplog.text
