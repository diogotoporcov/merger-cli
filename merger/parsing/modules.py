import importlib.util
import re
import shutil
from inspect import isclass
from pathlib import Path
from types import ModuleType
from typing import Type, Dict, Any, Set

from merger.parsing.default_parser import DefaultParser
from merger.utils.hash import hash_from_file
from merger.utils.json import write_json
from .parser import Parser
from ..exceptions.exceptions import InvalidModule, ModuleAlreadyInstalled
from ..utils.config import get_or_create_parsers_dir, get_or_create_config, get_config_path

_EXTENSION_REGEX_STR = r"\.[a-z0-9.]+$"
_EXTENSION_REGEX = re.compile(_EXTENSION_REGEX_STR, re.IGNORECASE)

_PARSERS: Dict[str, Type[Parser]]


def get_parser(filename: str) -> Type[Parser]:
    for extension, parser in _PARSERS.items():
        if filename.lower().endswith(extension.lower()):
            return parser

    return DefaultParser


def module_from_path(path: Path, name: str) -> ModuleType:
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
        raise ImportError(f"Error while loading module at {path}") from e

    return module


def get_parser_cls_from_module(module: ModuleType) -> Type[Parser]:
    try:
        parser_cls = getattr(module, "parser_cls")

    except AttributeError as e:
        raise InvalidModule(
            module.__file__,
            "parser attribute not provided",
        ) from e

    if not isclass(parser_cls) or not issubclass(parser_cls, Parser):
        raise InvalidModule(
            module.__file__,
            "parser is not a subclass of Parser",
        )

    extensions = getattr(parser_cls, "EXTENSIONS", None)
    if extensions is None:
        raise InvalidModule(
            module.__file__,
            "parser does not contain EXTENSIONS attribute",
        )

    if not isinstance(extensions, Set):
        raise InvalidModule(
            module.__file__,
            "parser EXTENSIONS attribute is not a set",
        )

    if not extensions:
        raise InvalidModule(
            module.__file__,
            "parser EXTENSSIONS attribute must contain at least one file extension"
        )

    for extension in extensions:
        if not isinstance(extension, str):
            raise InvalidModule(
                module.__file__,
                f"extension {extension!r} is not a string",
            )

        if not _EXTENSION_REGEX.fullmatch(extension):
            raise InvalidModule(
                module.__file__,
                f"extension {extension!r} does not match regex ({_EXTENSION_REGEX_STR})",
            )

    return parser_cls


def install_module(path: Path) -> None:
    config = get_or_create_config()
    modules = config.setdefault("modules", {})

    file_hash = hash_from_file(path, 8)
    filename = f"{file_hash}.py"

    if file_hash in modules:
        raise ModuleAlreadyInstalled(path.resolve().as_posix())

    module = module_from_path(path, file_hash)
    parser_cls = get_parser_cls_from_module(module)

    installed_extensions = {
        ext
        for module_entry in modules.values()
        for ext in module_entry.get("extensions", [])
    }

    overlapping = parser_cls.EXTENSIONS & installed_extensions
    if overlapping:
        raise ModuleAlreadyInstalled(
            f"Extensions already installed: {', '.join(sorted(overlapping))}"
        )

    module_path = get_or_create_parsers_dir() / filename
    shutil.copy(path, module_path)

    modules[file_hash] = {
        "extensions": list(parser_cls.EXTENSIONS),
        "path": module_path.as_posix(),
        "original_name": path.name,
    }

    write_json(get_config_path(), config)


def list_modules() -> Dict[str, Dict[str, Any]]:
    config = get_or_create_config()
    modules = config.setdefault("modules", {})
    return modules.copy()


def uninstall_module(module_id: str) -> None:
    config = get_or_create_config()
    modules = config.setdefault("modules", {})

    if module_id == "*":
        for id_, module_entry in list(modules.items()):
            module_path = Path(module_entry.get("path", ""))

            if module_path.exists():
                if not module_path.is_file():
                    raise IsADirectoryError(
                        f"Expected module file but found directory: {module_path}"
                    )
                module_path.unlink()

        modules.clear()
        write_json(get_config_path(), config)
        return

    if module_id not in modules:
        raise KeyError(f"Module not installed: {module_id}")

    module_entry = modules[module_id]
    module_path = Path(module_entry.get("path", ""))

    if module_path.exists():
        if not module_path.is_file():
            raise IsADirectoryError(
                f"Expected module file but found directory: {module_path}"
            )
        module_path.unlink()

    del modules[module_id]
    write_json(get_config_path(), config)


def load_parsers() -> Dict[str, Type[Parser]]:
    config = get_or_create_config()
    modules = config.get("modules", {})

    parsers: Dict[str, Type[Parser]] = {}

    for module_id, module_entry in modules.items():
        module_path = Path(module_entry.get("path", ""))

        if not module_path.exists():
            raise FileNotFoundError(
                f"Installed module file does not exist: {module_path}"
            )

        if not module_path.is_file():
            raise IsADirectoryError(
                f"Expected module file but found directory: {module_path}"
            )

        module = module_from_path(module_path, module_id)
        parser_cls = get_parser_cls_from_module(module)

        for extension in parser_cls.EXTENSIONS:
            if extension in parsers:
                raise InvalidModule(
                    module_path.as_posix(),
                    f"extension {extension!r} already registered "
                    f"by {parsers[extension].__module__}",
                )

            parsers[extension] = parser_cls

    return parsers


_PARSERS = load_parsers()
