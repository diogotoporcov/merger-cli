import importlib.metadata
import re
from pathlib import Path


def get_version() -> str:
    """
    Retrieve the version of the merger-cli package.
    Tries metadata for installed distributions first, then falls back to 
    parsing pyproject.toml for local development from source.
    """
    try:
        return importlib.metadata.version("merger-cli")
        
    except Exception:
        pass

    try:
        # Traverse the directory hierarchy to resolve the project's root from the current module.
        # This module is located at 'src/merger-cli/merger_cli/utils/version.py';
        path = Path(__file__).resolve().parents[4] / "pyproject.toml"
        if path.is_file():
            content = path.read_text(encoding="utf-8")
            match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
                
    except Exception:
        pass

    return "unknown"
