from typing import Dict, Type, List

from .impl.directory_tree_exporter import DirectoryTreeExporter
from .impl.json_exporter import JsonExporter
from .impl.json_tree_exporter import JsonTreeExporter
from .impl.plain_text_exporter import PlainTextExporter
from .registry import list_exporters, load_exporter
from .tree_exporter import TreeExporter
from .impl.tree_with_plain_text_exporter import TreeWithPlainTextExporter

_STATIC_EXPORTERS: Dict[str, Type[TreeExporter]] = {
    TreeWithPlainTextExporter.NAME.upper(): TreeWithPlainTextExporter,
    DirectoryTreeExporter.NAME.upper(): DirectoryTreeExporter,
    PlainTextExporter.NAME.upper(): PlainTextExporter,
    JsonExporter.NAME.upper(): JsonExporter,
    JsonTreeExporter.NAME.upper(): JsonTreeExporter,
}

_EXPORTER_CACHE: Dict[str, Type[TreeExporter]] = {}


def _get_all_exporter_names() -> List[str]:
    names = list(_STATIC_EXPORTERS.keys())
    exporters_meta = list_exporters()
    for meta in exporters_meta.values():
        for name in meta.extensions:
            names.append(name.upper())

    return sorted(list(set(names)))


def get_exporter_strategy_names() -> List[str]:
    return _get_all_exporter_names()


def get_exporter_strategy(strategy_name: str) -> Type[TreeExporter]:
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
            cls = load_exporter(module_id)
            _EXPORTER_CACHE[strategy_name_upper] = cls
            return cls

    raise ValueError(f"Unknown tree exporter: {strategy_name}")
