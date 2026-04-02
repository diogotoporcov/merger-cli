import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

def get_project_metadata():
    """Extract name and version from pyproject.toml."""
    # Prioritize the API package as it's the one we publish to PyPI
    pyproject_path = Path("src/merger-api/pyproject.toml")
    if not pyproject_path.exists():
        pyproject_path = Path("pyproject.toml")
    
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found.")
        sys.exit(1)
    
    print(f"Checking version from: {pyproject_path}")
    content = pyproject_path.read_text(encoding="utf-8")
    name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
    
    if not name_match or not version_match:
        print("Error: Could not find name or version in pyproject.toml.")
        sys.exit(1)
        
    return name_match.group(1), version_match.group(1)

def get_repo_url():
    """Extract GitHub repository URL from pyproject.toml."""
    # We always use the root pyproject.toml for repo URL if available, 
    # but the API one should have it too.
    pyproject_path = Path("src/merger-api/pyproject.toml")
    if not pyproject_path.exists():
        pyproject_path = Path("pyproject.toml")
    
    content = pyproject_path.read_text(encoding="utf-8")
    repo_match = re.search(r'Homepage\s*=\s*"([^"]+)"', content)
    return repo_match.group(1) if repo_match else None

def check_pypi(package_name, version):
    """Check if a specific version exists on PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        print(f"Warning: PyPI returned HTTP {e.code}")
    except Exception as e:
        print(f"Warning: Failed to check PyPI: {e}")
    return False

def check_github_release(repo_url, version):
    """Check if a release with the given version (or v-prefixed version) exists on GitHub."""
    if not repo_url or "github.com" not in repo_url:
        return False
    
    # Extract owner and repo from URL
    # Handle both https://github.com/owner/repo and https://github.com/owner/repo/
    path_parts = repo_url.rstrip("/").split("/")
    if len(path_parts) < 2:
        return False
    
    owner = path_parts[-2]
    repo = path_parts[-1]
    
    # Check both "v1.2.3" and "1.2.3" tags
    for tag in [f"v{version}", version]:
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/tags/{tag}"
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "merger-cli-version-check")
            # Use token if available to avoid rate limiting
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                req.add_header("Authorization", f"token {token}")
                
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            print(f"Warning: GitHub API returned HTTP {e.code}")
        except Exception as e:
            print(f"Warning: Failed to check GitHub: {e}")
            break
            
    return False

def main():
    name, version = get_project_metadata()
    repo_url = get_repo_url()
    
    print(f"Project: {name}")
    print(f"Version: {version}")
    
    pypi_exists = check_pypi(name, version)
    github_exists = check_github_release(repo_url, version)
    
    print(f"Exists on PyPI: {pypi_exists}")
    print(f"Exists on GitHub: {github_exists}")
    
    # Logic for should_publish
    # We should publish if it's NOT on PyPI or NOT on GitHub releases
    # But usually, this script is used to prevent duplicate PyPI uploads.
    should_publish = not pypi_exists
    
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"package_name={name}\n")
            f.write(f"version={version}\n")
            f.write(f"pypi_exists={str(pypi_exists).lower()}\n")
            f.write(f"github_exists={str(github_exists).lower()}\n")
            f.write(f"should_publish={str(should_publish).lower()}\n")
            
    if pypi_exists:
        print(f"Version {version} already exists on PyPI.")
    else:
        print(f"Version {version} is new for PyPI.")
        
    if github_exists:
        print(f"Version {version} already exists on GitHub releases.")
    else:
        print(f"Version {version} is new for GitHub releases.")

if __name__ == "__main__":
    main()
