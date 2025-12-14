import os
import platform
from pathlib import Path


def get_merger_dir() -> Path:
    DIR_NAME = "merger-cli"

    match platform.system():
        case "Windows":
            base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
            return Path(base) / DIR_NAME / "parsers"

        case "Darwin":
            return Path.home() / "Library" / "Application Support" / DIR_NAME

        case _:
            base = os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")
            return Path(base) / DIR_NAME / "parsers"


def get_parsers_dir() -> Path:
    merger_dir = get_merger_dir() / "parsers"
    merger_dir.mkdir(parents=True, exist_ok=True)
    return merger_dir
