import importlib.util
import shutil
from inspect import isclass
from pathlib import Path
from types import ModuleType
from typing import Type, Dict, List, Callable, Optional, TypeVar, Generic

from .config import get_or_create_config, save_config, ModuleEntry
from .hash import hash_from_file
from ..exceptions import InvalidModule, ModuleAlreadyInstalled
from ..logging import logger

T = TypeVar("T")


class ModuleManager(Generic[T]):
    def __init__(
        self,
        module_type_name: str,
        base_class: Type[T],
        config_key: str,
        get_target_dir: Callable[[], Path],
        class_attr: str,
        key_getter: Callable[[Type[T]], List[str]],
        validate_func: Optional[Callable[[Type[T], Path], None]] = None,
    ):
        self.module_type_name = module_type_name
        self.base_class = base_class
        self.config_key = config_key
        self.get_target_dir = get_target_dir
        self.class_attr = class_attr
        self.key_getter = key_getter
        self.validate_func = validate_func

    def _get_config_dict(self, config) -> Dict[str, ModuleEntry]:
        return getattr(config, self.config_key)

    @staticmethod
    def load_module_from_path(path: Path, name: str) -> ModuleType:
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        if not path.is_file():
            raise IsADirectoryError(f"Path exists but is not a file: {path}")

        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Failed to create import spec for module at {path}")

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            
        except Exception as e:
            raise ImportError(f"{type(e).__name__}: {e}") from e

        return module

    def get_class_from_module(self, module: ModuleType) -> Type[T]:
        try:
            cls = getattr(module, self.class_attr)
            
        except AttributeError as e:
            raise InvalidModule(
                getattr(module, "__file__", "unknown"),
                f"{self.class_attr} attribute not provided",
            ) from e

        if not isclass(cls) or not issubclass(cls, self.base_class):
            raise InvalidModule(
                getattr(module, "__file__", "unknown"),
                f"{self.class_attr} is not a subclass of {self.base_class.__name__}",
            )

        if self.validate_func:
            self.validate_func(cls, Path(getattr(module, "__file__", "")))

        return cls

    def install(self, path: Path) -> None:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")

        config = get_or_create_config()
        modules_dict = self._get_config_dict(config)

        file_hash = hash_from_file(path, 8)
        filename = f"{file_hash}.py"

        if file_hash in modules_dict:
            raise ModuleAlreadyInstalled(path.resolve().as_posix())

        module = self.load_module_from_path(path, file_hash)
        cls = self.get_class_from_module(module)

        target_dir = self.get_target_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        module_path = target_dir / filename
        shutil.copy(path, module_path)

        extensions = []
        if hasattr(cls, "EXTENSIONS"):
            extensions = list(getattr(cls, "EXTENSIONS"))
        elif hasattr(cls, "FILE_EXTENSION"):
            extensions = [getattr(cls, "FILE_EXTENSION")]

        modules_dict[file_hash] = ModuleEntry(
            extensions=extensions,
            path=module_path.as_posix(),
            original_name=path.name,
        )

        save_config(config)

    def uninstall(self, module_id: str) -> None:
        config = get_or_create_config()
        modules_dict = self._get_config_dict(config)

        if module_id == "*":
            for entry in list(modules_dict.values()):
                path = Path(entry.path)
                if path.exists() and path.is_file():
                    path.unlink()
            modules_dict.clear()
            save_config(config)
            return

        if module_id not in modules_dict:
            raise KeyError(f"{self.module_type_name.capitalize()} module not installed: {module_id}")

        entry = modules_dict[module_id]
        path = Path(entry.path)
        if path.exists() and path.is_file():
            path.unlink()

        del modules_dict[module_id]
        save_config(config)

    def list(self) -> Dict[str, ModuleEntry]:
        config = get_or_create_config()
        return self._get_config_dict(config).copy()

    def get_module_type(self, path: Path) -> str:
        """Detect the module type by checking its class inheritance."""
        try:
            module = self.load_module_from_path(path, "temp_type_check")
            cls = getattr(module, self.class_attr)
            if isclass(cls) and issubclass(cls, self.base_class):
                return self.module_type_name
            
        except AttributeError:
            pass
            
        except Exception:
            raise
            
        return "unknown"

    def load_all(self) -> Dict[str, Type[T]]:
        config = get_or_create_config()
        modules_dict = self._get_config_dict(config)
        loaded: Dict[str, Type[T]] = {}

        for module_id, entry in modules_dict.items():
            path = Path(entry.path)
            if not path.exists() or not path.is_file():
                continue

            try:
                module = self.load_module_from_path(path, module_id)
                cls = self.get_class_from_module(module)

                for key in self.key_getter(cls):
                    loaded[key] = cls
                    
            except (ImportError, InvalidModule) as e:
                logger.error(f"Failed to load {self.module_type_name} module '{module_id}' from {path}: {e}")
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error loading {self.module_type_name} module '{module_id}' from {path}: {e}")
                continue

        return loaded
