from pathlib import Path
from typing import Type
from types import ModuleType

from merger_plugin_api import TreeExporter
from ..exceptions import InvalidPlugin
from ..utils.config import get_or_create_exporters_dir
from ..utils.plugin_loader import PluginManager


def _validate_exporter_plugin(path: Path, module: ModuleType) -> None:
    if not getattr(module, "NAME", None):
        raise InvalidPlugin(path.as_posix(), "Exporter plugin does not contain NAME attribute")

    if not getattr(module, "FILE_EXTENSION", None):
        raise InvalidPlugin(path.as_posix(), "Exporter plugin does not contain FILE_EXTENSION attribute")


_manager = PluginManager[TreeExporter](
    plugin_type_name="exporter",
    base_class=TreeExporter,
    get_target_dir=get_or_create_exporters_dir,
    class_attr="exporter_cls",
    key_getter=lambda module: [getattr(module, "NAME").upper()],
    validate_func=_validate_exporter_plugin,
)

install_exporter = _manager.install
uninstall_exporter = _manager.uninstall
list_exporters = _manager.list
load_exporters = _manager.load_all
load_exporter = _manager.load_plugin
load_exporter_and_plugin = _manager.load_plugin_and_class
validate_exporters = _manager.validate_all
get_exporter_plugin_type = _manager.get_plugin_type
