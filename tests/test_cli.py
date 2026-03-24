import sys
from unittest.mock import patch

import pytest
from merger.cli import main


def test_cli_help(capsys):
    with patch.object(sys, 'argv', ['merger', '--help']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0
        captured = capsys.readouterr()
        assert "Merge files from a directory into a structured output" in captured.out

def test_cli_create_ignore(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with patch.object(sys, 'argv', ['merger', '-c', 'PYTHON']):
        main()
    
    assert (tmp_path / "merger.ignore").exists()
    content = (tmp_path / "merger.ignore").read_text()
    assert "__pycache__/" in content

def test_cli_version(capsys):
    with patch.object(sys, 'argv', ['merger', '--version']):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 0
        captured = capsys.readouterr()
        assert "merger" in captured.out or captured.err # argparse might use stderr for version in some python versions

def test_cli_merge_basic(tmp_path, monkeypatch, capsys):
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    (project_dir / "file1.txt").write_text("hello", encoding="utf-8")
    
    # Create required ignore file
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

def test_cli_merge_cli_ignore(tmp_path, monkeypatch, capsys):
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

def test_cli_create_ignore_invalid_template(capsys):
    with patch.object(sys, 'argv', ['merger', '-c', 'INVALID']):
        with pytest.raises(SystemExit) as e:
            main()
        # argparse raises SystemExit with code 2 for invalid choices
        assert e.value.code == 2

def test_cli_merge_missing_ignore(tmp_path, monkeypatch, capsys):
    project_dir = tmp_path / "myproj"
    project_dir.mkdir()
    
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    
    monkeypatch.chdir(tmp_path)
    
    # Run without creating merger.ignore
    with patch.object(sys, 'argv', ['merger', str(project_dir), str(output_dir)]):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 2
    
    captured = capsys.readouterr()
    err = " ".join(captured.err.split())
    assert f"Ignore file 'merger.ignore' is required" in err
    assert "You can create one using 'merger -c [TEMPLATE]'" in err
    assert "Available templates: CPP, CSHARP, DEFAULT, GO, JAVA, JAVASCRIPT, KOTLIN, PHP, PYTHON, RUST, TYPESCRIPT" in err

    # Check order
    instruction_idx = err.find("You can create one using 'merger -c [TEMPLATE]'")
    templates_idx = err.find("Available templates:")
    assert instruction_idx < templates_idx
