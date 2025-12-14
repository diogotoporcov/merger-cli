import importlib.util
import os
import re
import secrets
import shutil
from inspect import isclass
from pathlib import Path
from types import ModuleType
from typing import Iterable, Type, Dict, List, Tuple, Set

from .default_parser import DefaultParser
from ..exceptions.exceptions import InvalidParserFile
from ..logging.logger import logger
from .parser import Parser
from ..utils.merger_dir import get_parsers_dir


_EXTENSION_REGEX = re.compile(r"\.[a-z0-9.]+$", re.IGNORECASE)


def validate_module(module: ModuleType) -> bool:
    logger.debug(f"Validating parser module: {module.__name__}")

    all_names = getattr(module, "__all__", None)
    if not isinstance(all_names, (list, tuple)):
        logger.debug(f"Module {module.__name__} rejected: __all__ missing or invalid")
        return False

    if len(all_names) != 2:
        logger.debug(
            f"Module {module.__name__} rejected: __all__ must contain exactly 2 items"
        )
        return False

    try:
        exported = {name: getattr(module, name) for name in all_names}
    except AttributeError as exc:
        logger.debug(
            f"Module {module.__name__} rejected: failed to resolve __all__ exports ({exc})"
        )
        return False

    if "EXTENSIONS" not in exported:
        logger.debug(f"Module {module.__name__} rejected: EXTENSIONS not exported")
        return False

    extensions = exported["EXTENSIONS"]
    if not isinstance(extensions, Iterable):
        logger.debug(f"Module {module.__name__} rejected: EXTENSIONS is not iterable")
        return False

    for ext in extensions:
        if not isinstance(ext, str):
            logger.debug(
                f"Module {module.__name__} rejected: extension {ext!r} is not a string"
            )
            return False

        if not _EXTENSION_REGEX.fullmatch(ext):
            logger.debug(
                f"Module {module.__name__} rejected: extension {ext!r} does not match regex"
            )
            return False

    other_items = [value for name, value in exported.items() if name != "EXTENSIONS"]
    if len(other_items) != 1:
        logger.debug(
            f"Module {module.__name__} rejected: expected exactly one Parser class export"
        )
        return False

    candidate = other_items[0]
    if not isclass(candidate):
        logger.debug(
            f"Module {module.__name__} rejected: exported parser is not a class"
        )
        return False

    if not issubclass(candidate, Parser):
        logger.debug(
            f"Module {module.__name__} rejected: {candidate.__name__} does not subclass Parser"
        )
        return False

    logger.debug(f"Module {module.__name__} validated successfully")
    return True


def load_module_from_path(path: Path) -> ModuleType:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    module_name = secrets.token_urlsafe(8)

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to create import spec for module at {path}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)

    except Exception as e:
        raise ImportError(f"Error while loading module at {path}") from e

    return module


def get_parser_from_module(module: ModuleType) -> Tuple[Set[str], Type[Parser]]:
    extensions: Set[str] = set(module.EXTENSIONS)
    parser_cls: Type[Parser] = next(
        getattr(module, name)
        for name in module.__all__
        if name != "EXTENSIONS"
    )

    return extensions, parser_cls


def import_parser(path: Path) -> None:
    module = load_module_from_path(path)

    if not validate_module(module):
        raise InvalidParserFile(f"Parser module does not follow required interface: {path}")

    shutil.copy(path, get_parsers_dir())


def get_installed_parsers() -> Dict[str, Type[Parser]]:
    parsers: Dict[str, Type[Parser]] = {}

    logger.debug(f"Loading parsers")
    for path in get_parsers_dir().glob("*.py"):
        if path.name == "__init__.py":
            continue

        try:
            module = load_module_from_path(path)

        except ImportError as e:
            logger.debug(f"Skipping module {path.name}: {e}")
            continue

        extensions, parser_cls = get_parser_from_module(module)
        for extension in extensions:
            parsers[extension.lower()] = parser_cls

    logger.debug(f"Finished loading parsers. Total registered: {len(parsers)}")
    return parsers


_PARSERS = get_installed_parsers()


def get_parser(filename: str) -> Type[Parser]:
    for extension, parser in _PARSERS.items():
        if filename.lower().endswith(extension.lower()):
            return parser

    return DefaultParser


# TODO: Rewrite all of the below
def remove_parser(extension: str) -> None:
    if extension not in _PARSERS:
        logger.warning(f"No parser registered for extension '{extension}'")
        raise ValueError(f"No parser found for extension '{extension}'")

    parser_cls = _PARSERS.pop(extension)
    logger.info(f"Removed parser '{parser_cls.__name__}' for extension '{extension}'")

    parsers_dir = get_parsers_dir()
    parser_file = None
    for path in parsers_dir.glob("*.py"):
        if path.name == "__init__.py":
            continue

        module = load_module_from_path(path)
        if module and hasattr(module, "EXTENSIONS") and extension in module.EXTENSIONS:
            parser_file = path
            break

    if parser_file:
        try:
            os.remove(parser_file)
            logger.info(f"Removed parser module file: {parser_file}")

        except Exception as e:
            logger.error(f"Failed to remove parser module file '{parser_file}': {e}")
            raise ValueError(f"Failed to remove parser module file for extension '{extension}'")
    else:
        logger.warning(f"No parser module file found for extension '{extension}'")


def list_installed_parsers() -> Dict[str, List[str]]:
    installed: Dict[str, List[str]] = {}
    parsers_dir = get_parsers_dir()

    logger.debug(f"Listing installed parsers from directory: {parsers_dir}")

    for path in parsers_dir.glob("*.py"):
        if path.name == "__init__.py":
            continue

        module = load_module_from_path(path)
        if module is None:
            logger.debug(f"Skipping {path.name}: failed to load")
            continue

        if not validate_module(module):
            logger.warning(f"Skipping {path.name}: invalid parser module")
            continue

        module_name = path.stem
        extensions = list(module.EXTENSIONS)

        installed[str(path)] = extensions

        logger.debug(
            f"Found parser '{module_name}' handling extensions: {extensions}"
        )

    logger.debug(f"Total installed custom parsers found: {len(installed)}")
    return installed
