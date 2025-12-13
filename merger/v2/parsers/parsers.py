import importlib.util
import re
from inspect import isclass
from pathlib import Path
from types import ModuleType
from typing import Iterable, Type, Dict

from .default_parser import DefaultParser
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


def load_parsers() -> Dict[str, Type[Parser]]:
    parsers: Dict[str, Type[Parser]] = {}
    parsers_dir = get_parsers_dir()

    logger.debug(f"Loading parsers from directory: {parsers_dir}")

    def load_module_from_path(path: Path) -> ModuleType | None:
        module_name = f"_parser_{path.stem}"
        logger.debug(f"Attempting to load parser module from {path}")

        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            logger.warning(f"Failed to create spec for parser module: {path}")
            return None

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception:
            logger.exception(f"Exception while loading parser module: {path}")
            return None

        return module

    for path in parsers_dir.glob("*.py"):
        if path.name == "__init__.py":
            continue

        module = load_module_from_path(path)
        if module is None:
            logger.debug(f"Skipping module {path.name}: failed to load")
            continue

        if not validate_module(module):
            logger.warning(f"Skipping module {path.name}: invalid parser")
            continue

        extensions: Iterable[str] = module.EXTENSIONS
        parser_cls = next(
            getattr(module, name)
            for name in module.__all__
            if name != "EXTENSIONS"
        )

        for extension in extensions:
            if extension in parsers:
                logger.error(
                    f"Duplicate parser for extension '{extension}': "
                    f"{parsers[extension].__name__} vs {parser_cls.__name__}"
                )
                raise ValueError(
                    f"Duplicate parser for extension '{extension}' "
                    f"({parsers[extension].__name__} vs {parser_cls.__name__})"
                )

            parsers[extension] = parser_cls
            logger.info(
                f"Registered parser {parser_cls.__name__} for extension '{extension}'"
            )

    logger.debug(f"Finished loading parsers. Total registered: {len(parsers)}")
    return parsers


_PARSERS = load_parsers()


def get_parser(filename: str) -> Type[Parser]:
    for extension, parser in _PARSERS.values():
        if filename.endswith(extension):
            return parser

    return DefaultParser
