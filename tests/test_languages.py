from pathlib import Path
from unittest.mock import patch

import pytest
from merger.utils.ignore_templates import read_ignore_template
from merger.utils.patterns import matches_pattern


def check_template(template_name, path_to_test, should_match=True):
    body = read_ignore_template(template_name)
    patterns = [line.strip() for line in body.splitlines() if line.strip() and not line.startswith("#")]
    
    root = Path("/root")
    path = root / path_to_test
    
    # Checking if ANY pattern in the template matches the path
    matched = any(matches_pattern(path, root, p) for p in patterns)
    assert matched == should_match, f"Template {template_name} {'should' if should_match else 'should not'} match {path_to_test}"

@pytest.mark.parametrize("template,path,should_match", [
    ("PYTHON", "__pycache__/", True),
    ("PYTHON", ".venv/", True),
    ("PYTHON", "src/main.py", False),
    
    ("JAVASCRIPT", "node_modules/", True),
    ("JAVASCRIPT", "dist/", True),
    ("JAVASCRIPT", "src/app.ts", False),
    ("JAVASCRIPT", "lib/", True),
    ("JAVASCRIPT", "test.js.map", True),
    
    ("TYPESCRIPT", "node_modules/", True),
    ("TYPESCRIPT", "dist/", True),
    ("TYPESCRIPT", "tsconfig.tsbuildinfo", True),
    ("TYPESCRIPT", "lib/", True),
    ("TYPESCRIPT", "test.js.map", True),
    ("TYPESCRIPT", "test.d.ts.map", True),
    
    ("GO", "vendor/", True),
    ("GO", "bin/", True),
    
    ("RUST", "target/", True),
    ("RUST", "Cargo.lock", True),
    
    ("JAVA", "target/", True),
    ("JAVA", ".gradle/", True),
    
    ("CPP", "build/", True),
    ("CPP", "a.out", True),
    
    ("CSHARP", "bin/", True),
    ("CSHARP", ".vs/", True),
    
    ("PHP", "vendor/", True),
    ("PHP", ".env", True),
    
    ("KOTLIN", "build/", True),
])
def test_language_templates(template, path, should_match):
    # Some patterns might require directory vs. file distinction
    # For testing purposes, directories are assumed if they end with / in the test path
    # or if they are common directory names.
    
    # Mock is_dir() for the path
    is_dir = path.endswith("/") or "." not in path.split("/")[-1]
    
    with patch("pathlib.Path.is_dir", return_value=is_dir):
        check_template(template, path, should_match)
