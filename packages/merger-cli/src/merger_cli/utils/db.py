import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        self._data: Dict[str, Any] = {
            "plugins": {},
            "dependencies": [],
            "plugin_dependencies": []
        }
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            self._load()
            self._loaded = True

    def _load(self) -> None:
        if not self.db_path.exists():
            return

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)

        except (json.JSONDecodeError, OSError):
            self._data = {
                "plugins": {},
                "dependencies": [],
                "plugin_dependencies": []
            }

    def _save(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.db_path.with_suffix(".tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

        temp_path.replace(self.db_path)

    def add_plugin(self, plugin: PluginRecord) -> None:
        self._ensure_loaded()
        self._data["plugins"][plugin.id] = asdict(plugin)
        self._save()

    def remove_plugin(self, plugin_id: str) -> List[str]:
        """Removes the plugin and returns a list of dependencies that are no longer used."""
        self._ensure_loaded()

        if plugin_id not in self._data["plugins"]:
            return []

        # Get current dependencies for this plugin
        plugin_deps = [
            pd["dependency_name"]
            for pd in self._data["plugin_dependencies"]
            if pd["plugin_id"] == plugin_id
        ]

        # Delete plugin record
        del self._data["plugins"][plugin_id]

        # Delete plugin dependencies associations
        self._data["plugin_dependencies"] = [
            pd for pd in self._data["plugin_dependencies"]
            if pd["plugin_id"] != plugin_id
        ]

        # Identify dependencies that are now unused
        unused_deps: List[str] = []
        for dep in plugin_deps:
            is_used = any(
                pd["dependency_name"] == dep
                for pd in self._data["plugin_dependencies"]
            )

            if not is_used:
                unused_deps.append(dep)
                if dep in self._data["dependencies"]:
                    self._data["dependencies"].remove(dep)

        self._save()
        return unused_deps

    def add_plugin_dependency(self, plugin_id: str, dependency_name: str) -> None:
        self._ensure_loaded()

        if dependency_name not in self._data["dependencies"]:
            self._data["dependencies"].append(dependency_name)

        exists = any(
            pd["plugin_id"] == plugin_id and pd["dependency_name"] == dependency_name
            for pd in self._data["plugin_dependencies"]
        )

        if not exists:
            self._data["plugin_dependencies"].append({
                "plugin_id": plugin_id,
                "dependency_name": dependency_name
            })

        self._save()

    def get_plugin(self, plugin_id: str) -> Optional[PluginRecord]:
        self._ensure_loaded()
        plugin_data = self._data["plugins"].get(plugin_id)

        if not plugin_data:
            return None

        return PluginRecord(**plugin_data)

    def list_plugins(self, plugin_type: Optional[str] = None) -> List[PluginRecord]:
        self._ensure_loaded()
        plugins: List[PluginRecord] = []

        for p in self._data["plugins"].values():
            if not plugin_type or p["type"] == plugin_type:
                plugins.append(PluginRecord(**p))

        return plugins

    def get_unused_dependencies(self) -> List[str]:
        self._ensure_loaded()
        used_deps = {pd["dependency_name"] for pd in self._data["plugin_dependencies"]}
        return [d for d in self._data["dependencies"] if d not in used_deps]

    def clear_all(self) -> None:
        self._data = {
            "plugins": {},
            "dependencies": [],
            "plugin_dependencies": []
        }
        self._save()
