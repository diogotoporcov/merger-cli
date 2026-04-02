import importlib.metadata
import re
from pathlib import Path


_VERSION_CACHE = None


def get_version() -> str:
    """
    Retrieve the version of the merger-cli package.
    Tries metadata for installed distributions first, then falls back to 
    parsing pyproject.toml for local development from source.
    """
    global _VERSION_CACHE
    if _VERSION_CACHE is not None:
        return _VERSION_CACHE

    try:
        _VERSION_CACHE = importlib.metadata.version("merger-cli")
        return _VERSION_CACHE
        
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
                _VERSION_CACHE = match.group(1)
                return _VERSION_CACHE
                
    except Exception:
        pass

    _VERSION_CACHE = "unknown"
    return _VERSION_CACHE
