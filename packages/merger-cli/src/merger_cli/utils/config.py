import os
import platform
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel, Field

from .json import write_json, load_json


class PluginEntry(BaseModel):
    extensions: List[str]
    path: str
    original_name: str


class ConfigModel(BaseModel):
    version: int = Field(default=1)
    parsers: Dict[str, PluginEntry] = Field(default_factory=dict)
    exporters: Dict[str, PluginEntry] = Field(default_factory=dict)


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


def get_config_path() -> Path:
    return get_merger_dir() / "config.json"


def get_or_create_config() -> ConfigModel:
    config_path = get_config_path()
    if config_path.exists() and config_path.is_file():
        data = load_json(config_path)

        # Migration logic
        if "version" not in data:
            # Upgrade from v0 to v1
            data["version"] = 1
            if "parsers" not in data:
                if "modules" in data:
                    data["parsers"] = data.pop("modules")
                else:
                    data["parsers"] = {}
            if "exporters" not in data:
                data["exporters"] = {}
            
            config_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(config_path, data)

        return ConfigModel.model_validate(data)

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = ConfigModel()
    save_config(config)
    return config


def save_config(config: ConfigModel) -> None:
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(config_path, config.model_dump())
