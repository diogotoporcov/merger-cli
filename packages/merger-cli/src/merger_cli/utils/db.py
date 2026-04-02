import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

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
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.get_merger_dir() / "merger.db"
        self._initialized = False

    def _ensure_initialized(self):
        if not self._initialized:
            self._init_db()
            self._initialized = True

    def _get_connection(self):
        self._ensure_initialized()
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plugins (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    path TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    extensions TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dependencies (
                    name TEXT PRIMARY KEY
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS plugin_dependencies (
                    plugin_id TEXT,
                    dependency_name TEXT,
                    PRIMARY KEY (plugin_id, dependency_name),
                    FOREIGN KEY (plugin_id) REFERENCES plugins (id) ON DELETE CASCADE,
                    FOREIGN KEY (dependency_name) REFERENCES dependencies (name) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def add_plugin(self, plugin: PluginRecord):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO plugins (id, name, type, path, original_name, extensions) VALUES (?, ?, ?, ?, ?, ?)",
                (plugin.id, plugin.name, plugin.type, plugin.path, plugin.original_name, ",".join(plugin.extensions))
            )
            conn.commit()

    def remove_plugin(self, plugin_id: str) -> List[str]:
        """Removes the plugin and returns a list of dependencies that are no longer used."""
        with self._get_connection() as conn:
            # 1. Get current dependencies for this plugin
            cursor = conn.execute("SELECT dependency_name FROM plugin_dependencies WHERE plugin_id = ?", (plugin_id,))
            plugin_deps = [row[0] for row in cursor.fetchall()]

            # 2. Delete plugin (cascade will delete from plugin_dependencies)
            conn.execute("DELETE FROM plugins WHERE id = ?", (plugin_id,))
            conn.execute("DELETE FROM plugin_dependencies WHERE plugin_id = ?", (plugin_id,))

            # 3. Identify dependencies that are now unused
            unused_deps = []
            for dep in plugin_deps:
                cursor = conn.execute("SELECT COUNT(*) FROM plugin_dependencies WHERE dependency_name = ?", (dep,))
                if cursor.fetchone()[0] == 0:
                    unused_deps.append(dep)
                    conn.execute("DELETE FROM dependencies WHERE name = ?", (dep,))

            conn.commit()
            return unused_deps

    def add_plugin_dependency(self, plugin_id: str, dependency_name: str):
        with self._get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO dependencies (name) VALUES (?)", (dependency_name,))
            conn.execute("INSERT OR REPLACE INTO plugin_dependencies (plugin_id, dependency_name) VALUES (?, ?)",
                        (plugin_id, dependency_name))
            conn.commit()

    def get_plugin(self, plugin_id: str) -> Optional[PluginRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM plugins WHERE id = ?", (plugin_id,))
            row = cursor.fetchone()
            if row:
                return PluginRecord(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    path=row[3],
                    original_name=row[4],
                    extensions=row[5].split(",") if row[5] else []
                )
            return None

    def list_plugins(self, plugin_type: Optional[str] = None) -> List[PluginRecord]:
        with self._get_connection() as conn:
            if plugin_type:
                cursor = conn.execute("SELECT * FROM plugins WHERE type = ?", (plugin_type,))
            else:
                cursor = conn.execute("SELECT * FROM plugins")
            
            return [
                PluginRecord(
                    id=row[0],
                    name=row[1],
                    type=row[2],
                    path=row[3],
                    original_name=row[4],
                    extensions=row[5].split(",") if row[5] else []
                )
                for row in cursor.fetchall()
            ]

    def get_unused_dependencies(self) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT name FROM dependencies 
                WHERE name NOT IN (SELECT DISTINCT dependency_name FROM plugin_dependencies)
            """)
            return [row[0] for row in cursor.fetchall()]

    def clear_all(self):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM plugin_dependencies")
            conn.execute("DELETE FROM dependencies")
            conn.execute("DELETE FROM plugins")
            conn.commit()
