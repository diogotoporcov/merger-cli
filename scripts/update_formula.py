import sys
import re
from pathlib import Path

def update_formula(version, sha256):
    formula_path = Path("Formula/merger-cli.rb")
    if not formula_path.exists():
        print(f"Error: {formula_path} not found")
        sys.exit(1)
        
    content = formula_path.read_text()
    
    # Update URL - version is expected without 'v' prefix here, but the URL has 'v'
    # The release tag usually has 'v', e.g., v3.6.0
    v_version = version if version.startswith('v') else f'v{version}'
    
    # Replace URL
    # Matches /download/{{VERSION}}/ or /download/v3.6.0/ etc
    content = re.sub(
        r'url "https://github.com/diogotoporcov/merger-cli/releases/download/[^/]+/merger-cli-macos.tar.gz"',
        f'url "https://github.com/diogotoporcov/merger-cli/releases/download/{v_version}/merger-cli-macos.tar.gz"',
        content
    )
    
    # Replace SHA256 (both placeholder and existing hex)
    # Matches "REPLACE_WITH_ACTUAL_SHA256", "{{SHA256}}", or a 64-char hex string
    content = re.sub(
        r'sha256 "(?:REPLACE_WITH_ACTUAL_SHA256|\{\{SHA256\}\}|[a-fA-F0-9]{64})"',
        f'sha256 "{sha256}"',
        content
    )
    
    formula_path.write_text(content)
    print(f"Updated Formula/merger-cli.rb with version {v_version} and SHA256 {sha256}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python update_formula.py <version> <sha256>")
        sys.exit(1)
    update_formula(sys.argv[1], sys.argv[2])
