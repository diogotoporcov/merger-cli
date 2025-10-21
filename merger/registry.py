import importlib.util
import os
import platform
import shutil
from pathlib import Path
from typing import Tuple, Dict, Callable

from .logger import logger  # Adiciona o logger


def get_readers_folder() -> Path:
    system = platform.system()
    if system == "Windows":
        base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
        readers_dir = Path(base) / "Merger" / "installed_readers"
    elif system == "Darwin":
        readers_dir = Path.home() / "Library" / "Application Support" / "Merger" / "installed_readers"
    else:
        readers_dir = Path.home() / ".local" / "share" / "Merger" / "installed_readers"

    readers_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Readers directory resolved to: {readers_dir}")
    return readers_dir


def register_reader(extension: str, module_path: str):
    if not extension.startswith("."):
        raise ValueError("Extension must start with a dot, e.g. '.pdf'")

    module_path = Path(module_path).resolve()
    logger.debug(f"Registering reader for {extension} from {module_path}")

    try:
        spec = importlib.util.spec_from_file_location("temp_custom_reader", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        expected_all = {"reader", "validator"}
        actual_all = set(getattr(module, "__all__", {}))

        if actual_all != expected_all:
            raise ValueError(f"Invalid module: __all__ must be exactly {expected_all}, got {actual_all}")

        if not hasattr(module, "validator") or not callable(module.validator):
            raise ValueError("Module must define a callable 'validator'")

        if not hasattr(module, "reader") or not callable(module.reader):
            raise ValueError("Module must define a callable 'reader'")

        readers_dir = get_readers_folder()
        dest_path = readers_dir / f"{extension[1:]}.py"
        shutil.copy(module_path, dest_path)

        logger.info(f"Reader for '{extension}' registered successfully at '{dest_path}'")

    except Exception as e:
        logger.error(f"Failed to register reader for '{extension}': {e}")
        raise


def unregister_reader(extension: str):
    if not extension.startswith("."):
        raise ValueError("Extension must start with a dot, e.g. '.pdf'")

    readers_dir = get_readers_folder()
    target = readers_dir / f"{extension[1:]}.py"

    if target.exists():
        target.unlink()
        logger.info(f"Reader for '{extension}' unregistered (removed): {target}")
    else:
        logger.warning(f"No reader found to unregister for extension: '{extension}'")


def list_readers() -> Dict[str, str]:
    readers_dir = get_readers_folder()
    readers = {
        f".{f.stem}": str(f.resolve())
        for f in readers_dir.glob("*.py")
    }

    logger.debug(f"Listing installed readers: {readers}")
    return readers


def load_installed_readers() -> Tuple[Dict[str, Callable], Dict[str, Callable]]:
    readers_folder = get_readers_folder()
    validators = {}
    readers = {}

    for file in readers_folder.glob("*.py"):
        ext = f".{file.stem}"
        logger.debug(f"Loading reader module: {file}")

        try:
            spec = importlib.util.spec_from_file_location(f"reader_{file.stem}", file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            all_attr = getattr(module, "__all__", [])
            reader = getattr(module, "reader", None)
            validator = getattr(module, "validator", None)

            if "reader" not in all_attr or not callable(reader):
                logger.warning(f"Skipping invalid reader module '{file.name}': missing or invalid 'reader'")
                continue

            if "validator" in all_attr and not callable(validator):
                logger.warning(f"Skipping invalid validator in '{file.name}'")
                continue

            readers[ext] = reader
            validators[ext] = validator
            logger.debug(f"Loaded reader for {ext}")

        except Exception as e:
            logger.error(f"Failed to load reader from '{file}': {e}")

    return readers, validators


def load_custom_readers(module_path: Path) -> Tuple[Dict[str, Callable], Dict[str, Callable]]:
    logger.debug(f"Loading custom readers from: {module_path}")
    try:
        spec = importlib.util.spec_from_file_location("custom_readers_module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        readers = getattr(module, "readers", {})
        validators = getattr(module, "validators", {})
        logger.info(f"Custom readers loaded successfully from: {module_path}")
        return readers, validators

    except Exception as e:
        logger.error(f"Failed to load custom readers from {module_path}: {e}")
        raise
