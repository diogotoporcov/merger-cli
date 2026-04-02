import os
import platform
from pathlib import Path

def get_merger_dir() -> Path:
    dir_name = "merger-cli"

    system = platform.system()
    if system == "Windows":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
        return Path(base) / dir_name

    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / dir_name

    else:
        base = os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")
        return Path(base) / dir_name


def get_or_create_parsers_dir() -> Path:
    merger_dir = get_merger_dir() / "parsers"
    merger_dir.mkdir(parents=True, exist_ok=True)
    return merger_dir


def get_or_create_exporters_dir() -> Path:
    merger_dir = get_merger_dir() / "exporters"
    merger_dir.mkdir(parents=True, exist_ok=True)
    return merger_dir


def get_or_create_site_packages_dir() -> Path:
    """Returns the path to the directory where injected packages are installed."""
    merger_dir = get_merger_dir() / "site-packages"
    merger_dir.mkdir(parents=True, exist_ok=True)
    return merger_dir
