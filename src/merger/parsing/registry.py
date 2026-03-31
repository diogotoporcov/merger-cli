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
validate_parsers = _manager.validate_all
get_parser_module_type = _manager.get_module_type

_PARSER_CACHE: Dict[str, Type[Parser]] = {}


def get_parser(filename: str) -> Type[Parser]:
    filename_lower = filename.lower()
    parsers_meta = list_parsers()

    # Map extension to module_id
    ext_to_id: Dict[str, str] = {}
    for module_id, meta in parsers_meta.items():
        for ext in meta.extensions:
            ext_to_id[ext.lower()] = module_id

    # Try longest extensions first (e.g., .tar.gz before .gz)
    sorted_extensions = sorted(ext_to_id.keys(), key=len, reverse=True)
    for extension in sorted_extensions:
        if filename_lower.endswith(extension):
            module_id = ext_to_id[extension]
            if module_id in _PARSER_CACHE:
                return _PARSER_CACHE[module_id]

            cls = _manager.load_module(module_id)
            _PARSER_CACHE[module_id] = cls
            return cls

    return DefaultParser
