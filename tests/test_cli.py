import sys
from unittest.mock import patch

import pytest
from merger_cli.cli import main


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger_cli.utils.config.get_merger_dir", lambda: tmp_path)
    return tmp_path

def test_cli_help(capsys, mock_config_dir):
    with patch.object(sys, 'argv', ['merger', '--help']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0
        captured = capsys.readouterr()
        assert "Merger is a command-line utility for developers" in captured.out

def test_cli_create_ignore(tmp_path, monkeypatch, capsys, mock_config_dir):
    monkeypatch.chdir(tmp_path)
    with patch.object(sys, 'argv', ['merger', '-c', 'PYTHON']):
        main()
    
    assert (tmp_path / "merger.ignore").exists()
    content = (tmp_path / "merger.ignore").read_text()
    assert "__pycache__/" in content

def test_cli_version(capsys, mock_config_dir):
    with patch.object(sys, 'argv', ['merger', '--version']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0
        captured = capsys.readouterr()
        # RichHelpFormatter might use stdout or stderr for version
        all_out = captured.out + captured.err
        assert "merger" in all_out

def test_cli_merge_basic(tmp_path, monkeypatch, capsys, mock_config_dir):
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    (project_dir / "file1.txt").write_text("hello", encoding="utf-8")
    
    # Create required ignore file (optional now, but testing basic merge)
    (tmp_path / "merger.ignore").touch()
    
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    
    monkeypatch.chdir(tmp_path)
    
    with patch.object(sys, 'argv', ['merger', str(project_dir), str(output_dir), '-e', 'PLAIN_TEXT']):
        main()
    
    expected_output = output_dir / "merger.txt"
    assert expected_output.exists()
    content = expected_output.read_text()
    assert "hello" in content
    assert "<<FILE_START" in content

def test_cli_merge_cli_ignore(tmp_path, monkeypatch, capsys, mock_config_dir):
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    (project_dir / "file1.txt").write_text("hello", encoding="utf-8")
    (project_dir / "file2.log").write_text("log", encoding="utf-8")
    
    (tmp_path / "merger.ignore").touch()
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    
    monkeypatch.chdir(tmp_path)
    
    # Ignore .log files via CLI
    with patch.object(sys, 'argv', ['merger', str(project_dir), str(output_dir), '--ignore', '*.log']):
        main()
    
    expected_output = output_dir / "merger.txt"
    content = expected_output.read_text()
    assert "hello" in content
    assert "file2.log" not in content

def test_cli_create_ignore_invalid_template(capsys, mock_config_dir):
    with patch.object(sys, 'argv', ['merger', '-c', 'INVALID']):
        with pytest.raises(SystemExit) as e:
            main()
        # argparse raises SystemExit with code 2 for invalid choices
        assert e.value.code == 2

def test_cli_merge_no_ignore_file(tmp_path, monkeypatch, capsys, mock_config_dir):
    # Testing that it fails without merger.ignore
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    (project_dir / "file1.txt").write_text("hello", encoding="utf-8")
    
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    
    monkeypatch.chdir(tmp_path)
    
    # Run without creating merger.ignore
    with patch.object(sys, 'argv', ['merger', str(project_dir), str(output_dir)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2
    
    captured = capsys.readouterr()
    all_out = captured.out + captured.err
    assert "Ignore file 'merger.ignore' is required." in all_out
    assert "You can create one using 'merger -c [TEMPLATE]'." in all_out
    assert "Available templates:" in all_out

def test_cli_merge_qualifier_file_only(tmp_path, monkeypatch, capsys, mock_config_dir):
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    (project_dir / "data").mkdir()
    (project_dir / "data.txt").touch()
    
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    monkeypatch.chdir(tmp_path)
    
    # Create required ignore file
    (tmp_path / "merger.ignore").touch()
    
    # Ignore "data" but only if it's a file. Since "data" is a directory, it should NOT be ignored.
    with patch.object(sys, 'argv', ['merger', str(project_dir), str(output_dir), '--ignore', 'data:']):
        main()
    
    content = (output_dir / "merger.txt").read_text()
    assert "data/" in content
    assert "data.txt" in content

    # Ignore "data.txt" but only if it's a file.
    with patch.object(sys, 'argv', ['merger', str(project_dir), str(output_dir), '--ignore', 'data.txt:']):
        main()
    
    content = (output_dir / "merger.txt").read_text()
    assert "data.txt" not in content
