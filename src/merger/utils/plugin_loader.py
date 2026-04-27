import importlib.util
import shutil
from inspect import isclass
from pathlib import Path
from types import ModuleType
from typing import Type, Dict, List, Callable, Optional, TypeVar, Generic, Tuple

from .db import DatabaseManager, PluginRecord
from .hash import hash_from_file
from ..exceptions import InvalidPlugin, PluginAlreadyInstalled
from ..logging import logger

T = TypeVar("T")


class PluginManager(Generic[T]):
    def __init__(
        self,
        plugin_type_name: str,
        base_class: Type[T],
        get_target_dir: Callable[[], Path],
        class_attr: str,
        key_getter: Callable[[ModuleType], List[str]],
        validate_func: Optional[Callable[[Path, ModuleType], None]] = None,
    ):
        self.plugin_type_name = plugin_type_name
        self.base_class = base_class
        self.get_target_dir = get_target_dir
        self.class_attr = class_attr
        self.key_getter = key_getter
        self.validate_func = validate_func
        self._db: Optional[DatabaseManager] = None

    @property
    def db(self) -> DatabaseManager:
        if self._db is None:
            self._db = DatabaseManager()
        return self._db

    @staticmethod
    def load_plugin_from_path(path: Path, name: str) -> ModuleType:
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        if not path.is_file():
            raise IsADirectoryError(f"Path exists but is not a file: {path}")

        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to create import spec for plugin at {path}")

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            
        except Exception as e:
            raise ImportError(f"{type(e).__name__}: {e}") from e

        return module

    def get_class_from_plugin(self, module: ModuleType) -> Type[T]:
        try:
            cls = getattr(module, self.class_attr)
            
        except AttributeError as e:
            raise InvalidPlugin(
                getattr(module, "__file__", "unknown"),
                f"{self.class_attr} attribute not provided",
            ) from e

        if not isclass(cls) or not isinstance(cls, self.base_class):
            raise InvalidPlugin(
                getattr(module, "__file__", "unknown"),
                f"{self.class_attr} does not follow {self.base_class.__name__} protocol",
            )

        if self.validate_func:
            self.validate_func(Path(getattr(module, "__file__", "")), module)

        return cls

    def install(self, path: Path) -> None:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        file_hash = hash_from_file(path, 8)
        filename = f"{file_hash}.py"

        if self.db.get_plugin(file_hash):
            raise PluginAlreadyInstalled(path.resolve().as_posix())

        module = self.load_plugin_from_path(path, file_hash)
        _ = self.get_class_from_plugin(module) # Validation

        target_dir = self.get_target_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        plugin_path = target_dir / filename
        shutil.copy(path, plugin_path)

        extensions = self.key_getter(module)

        self.db.add_plugin(
            PluginRecord(
                id=file_hash,
                name=path.stem,
                type=self.plugin_type_name,
                path=plugin_path.as_posix(),
                original_name=path.name,
                extensions=extensions
            )
        )

    def uninstall(self, plugin_id: str) -> None:
        if plugin_id == "*":
            plugins = self.db.list_plugins(self.plugin_type_name)
            for p in plugins:
                self._uninstall_single(p.id)
            return

        self._uninstall_single(plugin_id)

    def _uninstall_single(self, plugin_id: str) -> None:
        plugin = self.db.get_plugin(plugin_id)
        if not plugin:
            raise KeyError(f"{self.plugin_type_name.capitalize()} plugin not installed: {plugin_id}")

        path = Path(plugin.path)
        if path.exists() and path.is_file():
            path.unlink()

        self.db.remove_plugin(plugin_id)

    def list(self) -> List[PluginRecord]:
        return self.db.list_plugins(self.plugin_type_name)

    def get_plugin_type(self, path: Path) -> str:
        """Detect the plugin type by checking its class inheritance."""
        try:
            module = self.load_plugin_from_path(path, "temp_type_check")
            cls = getattr(module, self.class_attr)
            if isclass(cls) and isinstance(cls, self.base_class):
                return self.plugin_type_name
            
        except AttributeError:
            pass
            
        except Exception:
            raise
            
        return "unknown"

    def load_plugin(self, plugin_id: str) -> Type[T]:
        _, cls = self.load_plugin_and_class(plugin_id)
        return cls

    def load_plugin_and_class(self, plugin_id: str) -> Tuple[ModuleType, Type[T]]:
        entry = self.db.get_plugin(plugin_id)

        if not entry:
            raise KeyError(f"{self.plugin_type_name.capitalize()} plugin not installed: {plugin_id}")

        path = Path(entry.path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Plugin file not found: {path}")

        module = self.load_plugin_from_path(path, plugin_id)
        cls = self.get_class_from_plugin(module)
        return module, cls

    def load_all(self) -> Dict[str, Type[T]]:
        plugins = self.db.list_plugins(self.plugin_type_name)
        loaded: Dict[str, Type[T]] = {}

        for entry in plugins:
            plugin_id = entry.id
            path = Path(entry.path)
            if not path.exists() or not path.is_file():
                continue

            try:
                module = self.load_plugin_from_path(path, plugin_id)
                cls = self.get_class_from_plugin(module)

                for key in self.key_getter(module):
                    loaded[key] = cls
                    
            except (ImportError, InvalidPlugin) as e:
                logger.error(f"Failed to load {self.plugin_type_name} plugin '{plugin_id}' from {path}: {e}")
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error loading {self.plugin_type_name} plugin '{plugin_id}' from {path}: {e}")
                continue

        return loaded

    def validate_all(self) -> None:
        plugins = self.db.list_plugins(self.plugin_type_name)

        for entry in plugins:
            plugin_id = entry.id
            path = Path(entry.path)
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"{self.plugin_type_name.capitalize()} plugin file not found: {path}")

            try:
                module = self.load_plugin_from_path(path, plugin_id)
                self.get_class_from_plugin(module)

            except (ImportError, InvalidPlugin) as e:
                raise InvalidPlugin(path.as_posix(), str(e)) from e

            except Exception as e:
                raise RuntimeError(f"Unexpected error validating {self.plugin_type_name} plugin '{plugin_id}': {e}") from e
