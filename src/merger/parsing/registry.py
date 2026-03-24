import re
from pathlib import Path
from typing import Type, Dict

from .impl.default_parser import DefaultParser
from .parser import Parser
from ..exceptions import InvalidModule
from ..utils.config import get_or_create_parsers_dir
from ..utils.module_manager import ModuleManager

_EXTENSION_REGEX_STR = r"\.[a-z0-9.]+$"
_EXTENSION_REGEX = re.compile(_EXTENSION_REGEX_STR, re.IGNORECASE)


def _validate_parser_cls(parser_cls: Type[Parser], path: Path) -> None:
    extensions = getattr(parser_cls, "EXTENSIONS", None)
    if extensions is None:
        raise InvalidModule(path.as_posix(), "parser does not contain EXTENSIONS attribute")

    if not isinstance(extensions, (set, list, tuple)):
        raise InvalidModule(path.as_posix(), "parser EXTENSIONS attribute is not a collection")

    if not extensions:
        raise InvalidModule(path.as_posix(), "parser EXTENSIONS attribute must contain at least one file extension")

    for extension in extensions:
        if not isinstance(extension, str):
            raise InvalidModule(path.as_posix(), f"extension {extension!r} is not a string")
        if not _EXTENSION_REGEX.fullmatch(extension):
            raise InvalidModule(path.as_posix(), f"extension {extension!r} does not match regex ({_EXTENSION_REGEX_STR})")


_manager = ModuleManager[Parser](
    module_type_name="parser",
    base_class=Parser,
    config_key="modules",
    get_target_dir=get_or_create_parsers_dir,
    class_attr="parser_cls",
    key_getter=lambda cls: [ext.lower() for ext in getattr(cls, "EXTENSIONS")],
    validate_func=_validate_parser_cls,
)

install_parser = _manager.install
uninstall_parser = _manager.uninstall
list_parsers = _manager.list
load_parsers = _manager.load_all
get_parser_module_type = _manager.get_module_type

_PARSERS: Dict[str, Type[Parser]] = load_parsers()


def get_parser(filename: str) -> Type[Parser]:
    filename_lower = filename.lower()
    # Try longest extensions first (e.g., .tar.gz before .gz)
    sorted_extensions = sorted(_PARSERS.keys(), key=len, reverse=True)
    for extension in sorted_extensions:
        if filename_lower.endswith(extension.lower()):
            return _PARSERS[extension]

    return DefaultParser
