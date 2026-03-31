import sys
from unittest.mock import patch
import pytest
from merger.cli import main
from pathlib import Path

def test_cli_exporter_case_insensitive(tmp_path, monkeypatch, capsys):
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    (project_dir / "file1.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "merger.ignore").touch()
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    
    # Use lowercase 'plain_text' which should be converted to 'PLAIN_TEXT'
    with patch.object(sys, 'argv', ['merger', str(project_dir), str(output_dir), '-e', 'plain_text']):
        main()
    
    expected_output = output_dir / "merger.txt"
    assert expected_output.exists()
    content = expected_output.read_text()
    assert "hello" in content

def test_cli_create_ignore_case_insensitive(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Use lowercase 'python'
    with patch.object(sys, 'argv', ['merger', '-c', 'python']):
        main()
    
    assert (tmp_path / "merger.ignore").exists()
    content = (tmp_path / "merger.ignore").read_text()
    assert "__pycache__/" in content

def test_cli_log_level_case_insensitive(tmp_path, monkeypatch, capsys):
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    (tmp_path / "merger.ignore").touch()
    monkeypatch.chdir(tmp_path)
    
    # Use lowercase 'debug'
    with patch.object(sys, 'argv', ['merger', str(project_dir), '--log-level', 'debug']):
        main()
    
    captured = capsys.readouterr()
    # If debug was set correctly, we might see debug messages in stderr if setup_logger worked
    # However, testing if it DIDN'T crash is already good enough as it would crash if 'debug' was invalid choice
