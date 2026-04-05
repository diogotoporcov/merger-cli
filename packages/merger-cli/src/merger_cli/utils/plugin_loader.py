import ast
import importlib.util
import shutil
from inspect import isclass
from pathlib import Path
from types import ModuleType
from typing import Type, Dict, List, Callable, Optional, TypeVar, Generic, Tuple

from .config import is_bundled
from .db import DatabaseManager, PluginRecord
from .dependencies import check_and_warn_dependencies
from .hash import hash_from_file
from .uv import uv_install, uv_purge, get_or_create_site_packages_dir
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
    def extract_requirements(path: Path) -> List[str]:
        """Extracts the REQUIREMENTS list from a Python file using AST without executing it."""
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                # Handle simple assignment: REQUIREMENTS = [...]
                is_req_assign = (
                    isinstance(node, ast.Assign) and
                    len(node.targets) == 1 and
                    isinstance(node.targets[0], ast.Name) and
                    node.targets[0].id == "REQUIREMENTS"
                )

                # Handle annotated assignment: REQUIREMENTS: List[str] = [...]
                is_req_ann_assign = (
                    isinstance(node, ast.AnnAssign) and
                    isinstance(node.target, ast.Name) and
                    node.target.id == "REQUIREMENTS" and
                    node.value is not None
                )

                if is_req_assign or is_req_ann_assign:
                    value_node = node.value if is_req_ann_assign else node.value
                    if isinstance(value_node, ast.List):
                        res = []
                        for elt in value_node.elts:
                            # In Python 3.14+, ast.Str and ast.Bytes are removed.
                            # ast.Constant is used since 3.8.
                            if hasattr(ast, "Constant") and isinstance(elt, ast.Constant):
                                res.append(elt.value)

                            elif hasattr(ast, "Str") and isinstance(elt, ast.Str):
                                res.append(elt.s)

                        return res

            return []

        except Exception as e:
            logger.warning(f"Could not parse REQUIREMENTS from {path}: {e}")
            return []

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

        if not isclass(cls) or not issubclass(cls, self.base_class):
            raise InvalidPlugin(
                getattr(module, "__file__", "unknown"),
                f"{self.class_attr} is not a subclass of {self.base_class.__name__}",
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

        # Handle dependencies BEFORE loading the module
        requirements = self.extract_requirements(path)
        if requirements:
            if is_bundled():
                logger.info(f"Installing dependencies for {self.plugin_type_name} plugin: {', '.join(requirements)}")
                site_packages = get_or_create_site_packages_dir()
                uv_install(requirements, target=site_packages)
            
            else:
                check_and_warn_dependencies(requirements, f"the {self.plugin_type_name} plugin")

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

        for dep in requirements:
            self.db.add_plugin_dependency(file_hash, dep)

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

        unused_deps = self.db.remove_plugin(plugin_id)
        if unused_deps and is_bundled():
            site_packages = get_or_create_site_packages_dir()
            uv_purge(unused_deps, target=site_packages)

    def list(self) -> List[PluginRecord]:
        return self.db.list_plugins(self.plugin_type_name)

    def get_plugin_type(self, path: Path) -> str:
        """Detect the plugin type by checking its class inheritance."""
        try:
            module = self.load_plugin_from_path(path, "temp_type_check")
            cls = getattr(module, self.class_attr)
            if isclass(cls) and issubclass(cls, self.base_class):
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
