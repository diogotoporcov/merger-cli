import re
from pathlib import Path
from types import ModuleType
from typing import Type, Dict

from .base import Parser
from ..exceptions import InvalidPlugin
from ..utils.config import get_or_create_parsers_dir
from ..utils.plugin_loader import PluginManager

_EXTENSION_REGEX_STR = r"\.[a-z0-9.]+$"
_EXTENSION_REGEX = re.compile(_EXTENSION_REGEX_STR, re.IGNORECASE)


def _validate_parser_plugin(path: Path, module: ModuleType) -> None:
    extensions = getattr(module, "EXTENSIONS", None)
    if extensions is None:
        raise InvalidPlugin(path.as_posix(), "Parser plugin does not contain EXTENSIONS attribute")

    if not isinstance(extensions, (set, list, tuple)):
        raise InvalidPlugin(path.as_posix(), "parser EXTENSIONS attribute is not a collection")

    if not extensions:
        raise InvalidPlugin(path.as_posix(), "parser EXTENSIONS attribute must contain at least one file extension")

    for extension in extensions:
        if not isinstance(extension, str):
            raise InvalidPlugin(path.as_posix(), f"extension {extension!r} is not a string")
        if not _EXTENSION_REGEX.fullmatch(extension):
            raise InvalidPlugin(path.as_posix(), f"extension {extension!r} does not match regex ({_EXTENSION_REGEX_STR})")


_manager = PluginManager[Parser](
    plugin_type_name="parser",
    base_class=Parser,
    get_target_dir=get_or_create_parsers_dir,
    class_attr="parser_cls",
    key_getter=lambda module: [ext.lower() for ext in getattr(module, "EXTENSIONS")],
    validate_func=_validate_parser_plugin,
)

install_parser = _manager.install
uninstall_parser = _manager.uninstall
list_parsers = _manager.list
load_parsers = _manager.load_all
validate_parsers = _manager.validate_all
get_parser_plugin_type = _manager.get_plugin_type

_PARSER_CACHE: Dict[str, Type[Parser]] = {}


def get_parser(filename: str) -> Type[Parser]:
    from .impl.default_parser import DefaultParser
    filename_lower = filename.lower()
    parsers_meta = list_parsers()

    # Map extension to plugin_id
    ext_to_id: Dict[str, str] = {}
    for meta in parsers_meta:
        for ext in meta.extensions:
            ext_to_id[ext.lower()] = meta.id

    # Try longest extensions first (e.g., .tar.gz before .gz)
    sorted_extensions = sorted(ext_to_id.keys(), key=len, reverse=True)
    for extension in sorted_extensions:
        if filename_lower.endswith(extension):
            plugin_id = ext_to_id[extension]
            if plugin_id in _PARSER_CACHE:
                return _PARSER_CACHE[plugin_id]

            cls = _manager.load_plugin(plugin_id)
            _PARSER_CACHE[plugin_id] = cls
            return cls

    return DefaultParser
