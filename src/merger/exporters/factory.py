from typing import Dict, Type, List

from .impl.directory_tree_exporter import DirectoryTreeExporter
from .impl.json_exporter import JsonExporter
from .impl.json_tree_exporter import JsonTreeExporter
from .impl.plain_text_exporter import PlainTextExporter
from .registry import load_exporters
from .tree_exporter import TreeExporter
from .impl.tree_with_plain_text_exporter import TreeWithPlainTextExporter

_STATIC_EXPORTERS: Dict[str, Type[TreeExporter]] = {
    TreeWithPlainTextExporter.NAME.upper(): TreeWithPlainTextExporter,
    DirectoryTreeExporter.NAME.upper(): DirectoryTreeExporter,
    PlainTextExporter.NAME.upper(): PlainTextExporter,
    JsonExporter.NAME.upper(): JsonExporter,
    JsonTreeExporter.NAME.upper(): JsonTreeExporter,
}


def _get_all_exporters() -> Dict[str, Type[TreeExporter]]:
    exporters = _STATIC_EXPORTERS.copy()
    try:
        exporters.update(load_exporters())

    except Exception:
        pass

    return exporters


def get_exporter_strategy_names() -> List[str]:
    return list(_get_all_exporters().keys())


def get_exporter_strategy(strategy_name: str) -> Type[TreeExporter]:
    exporters = _get_all_exporters()
    try:
        return exporters[strategy_name.upper()]

    except KeyError as e:
        raise ValueError(f"Unknown tree exporter: {strategy_name}") from e
