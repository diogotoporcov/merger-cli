import os
import platform
from pathlib import Path
from typing import Dict, Any

from .json import write_json, load_json


def get_merger_dir() -> Path:
    DIR_NAME = "merger-cli"

    match platform.system():
        case "Windows":
            base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
            return Path(base) / DIR_NAME

        case "Darwin":
            return Path.home() / "Library" / "Application Support" / DIR_NAME

        case _:
            base = os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")
            return Path(base) / DIR_NAME


def get_or_create_parsers_dir() -> Path:
    merger_dir = get_merger_dir() / "parsers"
    merger_dir.mkdir(parents=True, exist_ok=True)
    return merger_dir


def get_config_path() -> Path:
    return get_merger_dir() / "config.json"


def get_or_create_config() -> Dict[str, Dict[str, Any]]:
    config_path = get_config_path()
    if config_path.exists() and config_path.is_file():
        return load_json(config_path)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(config_path, {})
    return {}
