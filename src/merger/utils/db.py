import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from . import config


@dataclass
class PluginRecord:
    id: str
    name: str
    type: str
    path: str
    original_name: str
    extensions: List[str] = field(default_factory=list)


class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or config.get_merger_dir() / "merger.json"
        self._plugins: Dict[str, PluginRecord] = {}
        self._loaded = False

    @staticmethod
    def _coerce_record(plugin_id: str, value: object) -> Optional[PluginRecord]:
        if not isinstance(value, dict):
            return None

        record_id = value.get("id", plugin_id)
        name = value.get("name")
        plugin_type = value.get("type")
        path = value.get("path")
        original_name = value.get("original_name")
        if not isinstance(record_id, str):
            return None
        if not isinstance(name, str):
            return None
        if not isinstance(plugin_type, str):
            return None
        if not isinstance(path, str):
            return None
        if not isinstance(original_name, str):
            return None

        extensions = value.get("extensions", [])
        if not isinstance(extensions, list) or not all(isinstance(ext, str) for ext in extensions):
            return None

        return PluginRecord(
            id=record_id,
            name=name,
            type=plugin_type,
            path=path,
            original_name=original_name,
            extensions=extensions,
        )

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self._load()
            self._loaded = True

    def _load(self) -> None:
        if not self.db_path.exists():
            return

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        except (json.JSONDecodeError, OSError):
            self._plugins = {}
            return

        if not isinstance(data, dict):
            self._plugins = {}
            return

        raw_plugins = data.get("plugins")
        if not isinstance(raw_plugins, dict):
            self._plugins = {}
            return

        plugins: Dict[str, PluginRecord] = {}
        for plugin_id, raw_plugin in raw_plugins.items():
            if not isinstance(plugin_id, str):
                continue

            plugin = self._coerce_record(plugin_id, raw_plugin)
            if plugin is not None:
                plugins[plugin_id] = plugin

        self._plugins = plugins

    def _save(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.db_path.with_suffix(".tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "plugins": {
                        plugin_id: asdict(plugin)
                        for plugin_id, plugin in self._plugins.items()
                    }
                },
                f,
                indent=2,
            )

        temp_path.replace(self.db_path)

    def add_plugin(self, plugin: PluginRecord) -> None:
        self._ensure_loaded()
        self._plugins[plugin.id] = plugin
        self._save()

    def remove_plugin(self, plugin_id: str) -> None:
        self._ensure_loaded()

        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            self._save()

    def get_plugin(self, plugin_id: str) -> Optional[PluginRecord]:
        self._ensure_loaded()
        return self._plugins.get(plugin_id)

    def list_plugins(self, plugin_type: Optional[str] = None) -> List[PluginRecord]:
        self._ensure_loaded()
        plugins: List[PluginRecord] = []

        for plugin in self._plugins.values():
            if not plugin_type or plugin.type == plugin_type:
                plugins.append(plugin)

        return plugins

    def clear_all(self) -> None:
        self._plugins = {}
        self._save()
