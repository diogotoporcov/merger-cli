from typing import Dict, List

from .base import ExporterInfo
from .impl.json_exporter import JsonExporter
from .impl.json_tree_exporter import JsonTreeExporter
from .impl.text import TextExporter
from .impl.tree import TreeStructureExporter
from .impl.tree_text import TreeTextExporter
from .registry import list_exporters, load_exporter_and_plugin

_STATIC_EXPORTERS: Dict[str, ExporterInfo] = {
    TreeTextExporter.NAME.upper(): ExporterInfo(
        TreeTextExporter, TreeTextExporter.NAME, TreeTextExporter.FILE_EXTENSION
    ),
    TreeStructureExporter.NAME.upper(): ExporterInfo(
        TreeStructureExporter, TreeStructureExporter.NAME, TreeStructureExporter.FILE_EXTENSION
    ),
    TextExporter.NAME.upper(): ExporterInfo(
        TextExporter, TextExporter.NAME, TextExporter.FILE_EXTENSION
    ),
    JsonExporter.NAME.upper(): ExporterInfo(
        JsonExporter, JsonExporter.NAME, JsonExporter.FILE_EXTENSION
    ),
    JsonTreeExporter.NAME.upper(): ExporterInfo(
        JsonTreeExporter, JsonTreeExporter.NAME, JsonTreeExporter.FILE_EXTENSION
    ),
}

_EXPORTER_CACHE: Dict[str, ExporterInfo] = {}


def _get_all_exporter_names() -> List[str]:
    names = list(_STATIC_EXPORTERS.keys())
    exporters_meta = list_exporters()
    for meta in exporters_meta:
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

    # Loading from plugins
    exporters_meta = list_exporters()
    for meta in exporters_meta:
        if strategy_name_upper in [name.upper() for name in meta.extensions]:
            plugin_id = meta.id
            module, cls = load_exporter_and_plugin(plugin_id)
            info = ExporterInfo(
                cls=cls,
                name=cls.NAME,
                file_extension=cls.FILE_EXTENSION
            )
            _EXPORTER_CACHE[strategy_name_upper] = info
            return info

    raise ValueError(f"Unknown tree exporter: {strategy_name}")
