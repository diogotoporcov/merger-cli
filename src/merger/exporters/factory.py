from typing import Dict, Type, List, Optional, Any
from dataclasses import dataclass

from .impl.directory_tree_exporter import DirectoryTreeExporter, NAME as DIR_TREE_NAME
from .impl.json_exporter import JsonExporter, NAME as JSON_NAME
from .impl.json_tree_exporter import JsonTreeExporter, NAME as JSON_TREE_NAME
from .impl.plain_text_exporter import PlainTextExporter, NAME as PLAIN_TEXT_NAME
from .registry import list_exporters, load_exporter, load_exporter_and_module
from .tree_exporter import TreeExporter
from .impl.tree_with_plain_text_exporter import TreeWithPlainTextExporter, NAME as TREE_PLAIN_TEXT_NAME


@dataclass
class ExporterInfo:
    cls: Type[TreeExporter]
    name: str
    file_extension: str


_STATIC_EXPORTERS: Dict[str, ExporterInfo] = {
    TREE_PLAIN_TEXT_NAME.upper(): ExporterInfo(TreeWithPlainTextExporter, TREE_PLAIN_TEXT_NAME, ".txt"),
    DIR_TREE_NAME.upper(): ExporterInfo(DirectoryTreeExporter, DIR_TREE_NAME, ".txt"),
    PLAIN_TEXT_NAME.upper(): ExporterInfo(PlainTextExporter, PLAIN_TEXT_NAME, ".txt"),
    JSON_NAME.upper(): ExporterInfo(JsonExporter, JSON_NAME, ".json"),
    JSON_TREE_NAME.upper(): ExporterInfo(JsonTreeExporter, JSON_TREE_NAME, ".json"),
}

_EXPORTER_CACHE: Dict[str, ExporterInfo] = {}


def _get_all_exporter_names() -> List[str]:
    names = list(_STATIC_EXPORTERS.keys())
    exporters_meta = list_exporters()
    for meta in exporters_meta.values():
        for name in meta.extensions:
            names.append(name.upper())

    return sorted(list(set(names)))


def get_exporter_strategy_names() -> List[str]:
    return _get_all_exporter_names()


def get_exporter_strategy(strategy_name: str) -> ExporterInfo:
    strategy_name_upper = strategy_name.upper()

    # Static
    if strategy_name_upper in _STATIC_EXPORTERS:
        return _STATIC_EXPORTERS[strategy_name_upper]

    # Cache
    if strategy_name_upper in _EXPORTER_CACHE:
        return _EXPORTER_CACHE[strategy_name_upper]

    # Loading from modules
    exporters_meta = list_exporters()
    for module_id, meta in exporters_meta.items():
        if strategy_name_upper in [name.upper() for name in meta.extensions]:
            module, cls = load_exporter_and_module(module_id)
            info = ExporterInfo(
                cls=cls,
                name=getattr(module, "NAME"),
                file_extension=getattr(module, "FILE_EXTENSION")
            )
            _EXPORTER_CACHE[strategy_name_upper] = info
            return info

    raise ValueError(f"Unknown tree exporter: {strategy_name}")
