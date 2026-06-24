import re
from pathlib import Path
from types import ModuleType
from typing import Dict, List, Optional, Tuple, Type

from .base import Parser
from ..exceptions import InvalidPlugin
from ..utils.config import get_or_create_parsers_dir
from ..utils.plugin_loader import PluginManager

_EXTENSION_REGEX_STR = r"\.[a-z0-9.]+$"
_EXTENSION_REGEX = re.compile(_EXTENSION_REGEX_STR, re.IGNORECASE)


def _validate_parser_plugin(path: Path, _module: ModuleType, cls: Type[Parser]) -> None:
    extensions = getattr(cls, "EXTENSIONS", None)
    if extensions is None:
        raise InvalidPlugin(path.as_posix(), "Parser plugin class does not contain EXTENSIONS attribute")

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
    key_getter=lambda _module, cls: [ext.lower() for ext in cls.EXTENSIONS],
    validate_func=_validate_parser_plugin,
)

parser_registry = _manager
list_parsers = _manager.list
load_parsers = _manager.load_all
validate_parsers = _manager.validate_all
get_parser_plugin_type = _manager.get_plugin_type

_PARSER_CACHE: Dict[str, Type[Parser]] = {}
_EXTENSION_TO_PLUGIN_ID_CACHE: Optional[Dict[str, str]] = None
_SORTED_EXTENSIONS_CACHE: Optional[List[str]] = None


def _clear_parser_caches() -> None:
    global _EXTENSION_TO_PLUGIN_ID_CACHE, _SORTED_EXTENSIONS_CACHE
    _PARSER_CACHE.clear()
    _EXTENSION_TO_PLUGIN_ID_CACHE = None
    _SORTED_EXTENSIONS_CACHE = None


def install_parser(path: Path) -> None:
    _manager.install(path)
    _clear_parser_caches()


def uninstall_parser(plugin_id: str) -> None:
    _manager.uninstall(plugin_id)
    _clear_parser_caches()


def _get_extension_lookup() -> Tuple[Dict[str, str], List[str]]:
    global _EXTENSION_TO_PLUGIN_ID_CACHE, _SORTED_EXTENSIONS_CACHE
    if _EXTENSION_TO_PLUGIN_ID_CACHE is None or _SORTED_EXTENSIONS_CACHE is None:
        ext_to_id: Dict[str, str] = {}
        for meta in list_parsers():
            for ext in meta.extensions:
                ext_to_id[ext.lower()] = meta.id

        _EXTENSION_TO_PLUGIN_ID_CACHE = ext_to_id
        _SORTED_EXTENSIONS_CACHE = sorted(ext_to_id.keys(), key=len, reverse=True)

    return _EXTENSION_TO_PLUGIN_ID_CACHE, _SORTED_EXTENSIONS_CACHE


def get_parser(filename: str) -> Type[Parser]:
    from .impl.text import TextParser
    filename_lower = filename.lower()
    ext_to_id, sorted_extensions = _get_extension_lookup()

    # Try longest extensions first (e.g., .tar.gz before .gz)
    for extension in sorted_extensions:
        if filename_lower.endswith(extension):
            plugin_id = ext_to_id[extension]
            if plugin_id in _PARSER_CACHE:
                return _PARSER_CACHE[plugin_id]

            cls = _manager.load_plugin(plugin_id)
            _PARSER_CACHE[plugin_id] = cls
            return cls

    return TextParser
