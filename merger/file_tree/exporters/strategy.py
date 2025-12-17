from typing import Dict, Type, List

from .json_exporter import JsonExporter
from .tree_exporter import TreeExporter
from .json_tree_exporter import JsonTreeExporter
from .directory_tree_exporter import DirectoryTreeExporter
from .plain_text_exporter import PlainTextExporter
from .tree_with_plain_text_exporter import TreeWithPlainTextExporter

_EXPORTERS: Dict[str, Type[TreeExporter]] = {
    TreeWithPlainTextExporter.NAME.upper(): TreeWithPlainTextExporter,
    DirectoryTreeExporter.NAME.upper(): DirectoryTreeExporter,
    PlainTextExporter.NAME.upper(): PlainTextExporter,
    JsonExporter.NAME.upper(): JsonExporter,
    JsonTreeExporter.NAME.upper(): JsonTreeExporter,
}


def get_exporter_strategy_names() -> List[str]:
    return list(_EXPORTERS.keys())


def get_exporter_strategy(strategy_name: str) -> Type[TreeExporter]:
    try:
        return _EXPORTERS[strategy_name.upper()]

    except KeyError as e:
        raise ValueError(f"Unknown tree exporter: {strategy_name}") from e
