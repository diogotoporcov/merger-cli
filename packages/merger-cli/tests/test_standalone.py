import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def test_project(tmp_path):
    """Creates a temporary test project with some files and an ignore file."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "test.txt").write_text("Hello Standalone")
    (src / "ignored.txt").write_text("This should be ignored")
    (tmp_path / "merger.ignore").write_text("ignored.txt")
    return tmp_path

def run_merger(merger_bin, args, cwd=None):
    """Helper to run the merger binary with arguments."""
    if not merger_bin:
        pytest.skip("No merger binary provided for standalone tests. Use --merger-bin.")
    
    # Ensure binary exists and is executable
    bin_path = Path(merger_bin).resolve()
    if not bin_path.exists():
        pytest.fail(f"Merger binary not found at: {bin_path}")

    cmd = [str(bin_path)] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    return result

def test_version(merger_bin):
    """Verifies that 'merger --version' returns the expected version."""
    result = run_merger(merger_bin, ["--version"])
    assert result.returncode == 0
    # We don't assert the exact version to avoid breaking on every update, 
    # but it should look like a version number.
    assert "merger" in result.stdout.lower()
    import re
    assert re.search(r"\d+\.\d+\.\d+", result.stdout)

def test_help(merger_bin):
    """Verifies that 'merger --help' works."""
    result = run_merger(merger_bin, ["--help"])
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
    assert "--inject" in result.stdout

def test_basic_merge(merger_bin, test_project):
    """Verifies basic merge functionality and ignore support."""
    result = run_merger(merger_bin, ["."], cwd=test_project)
    assert result.returncode == 0
    
    output_file = test_project / "merger.txt"
    assert output_file.exists()
    
    content = output_file.read_text()
    assert "Hello Standalone" in content
    assert "This should be ignored" not in content

def test_json_export(merger_bin, test_project):
    """Verifies JSON export functionality."""
    result = run_merger(merger_bin, [".", "-e", "json"], cwd=test_project)
    assert result.returncode == 0
    
    output_file = test_project / "merger.json"
    assert output_file.exists()
    import json
    data = json.loads(output_file.read_text())
    assert isinstance(data, dict)
    assert any(p.endswith("test.txt") for p in data.keys())
    assert not any(p.endswith("ignored.txt") for p in data.keys())

@pytest.mark.parametrize("package", ["pyjokes"])
def test_injection_and_purge(merger_bin, package):
    """Verifies that package injection and purge commands don't crash."""
    # Note: Full functional test of injection is hard in a CI environment 
    # without proper pip/networking, but we check if the CLI handles the command.
    
    # Injection
    inject_result = run_merger(merger_bin, ["--inject", package])
    # Even if it fails due to network/pip issues, it shouldn't crash with a traceback
    if inject_result.returncode != 0:
        # If it fails, check it's a "clean" failure (not a Python crash)
        assert "Traceback" not in inject_result.stderr
        pytest.skip(f"Injection failed: {inject_result.stderr}")
    else:
        # Check both stdout and stderr because logging might go to either depending on config
        full_output = inject_result.stdout + inject_result.stderr
        assert "Injecting" in full_output or "Successfully" in full_output

    # Purge with non-interactive mode (--yes)
    purge_result = run_merger(merger_bin, ["--purge-packages", "--yes"])
    assert purge_result.returncode == 0
    full_output = purge_result.stdout + purge_result.stderr
    assert "All injected packages have been purged" in full_output or "No injected packages found to purge" in full_output

def test_invalid_arg(merger_bin):
    """Verifies that invalid arguments return non-zero exit code."""
    result = run_merger(merger_bin, ["--non-existent-arg"])
    assert result.returncode != 0
    assert "error" in result.stderr.lower()
