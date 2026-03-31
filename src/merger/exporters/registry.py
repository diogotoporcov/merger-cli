from pathlib import Path
from typing import Type

from .tree_exporter import TreeExporter
from ..exceptions import InvalidModule
from ..utils.config import get_or_create_exporters_dir
from ..utils.module_manager import ModuleManager


def _validate_exporter_cls(exporter_cls: Type[TreeExporter], path: Path) -> None:
    if not getattr(exporter_cls, "NAME", None):
        raise InvalidModule(path.as_posix(), "exporter does not contain NAME attribute")

    if not getattr(exporter_cls, "FILE_EXTENSION", None):
        raise InvalidModule(path.as_posix(), "exporter does not contain FILE_EXTENSION attribute")


_manager = ModuleManager[TreeExporter](
    module_type_name="exporter",
    base_class=TreeExporter,
    config_key="exporters",
    get_target_dir=get_or_create_exporters_dir,
    class_attr="exporter_cls",
    key_getter=lambda cls: [getattr(cls, "NAME").upper()],
    validate_func=_validate_exporter_cls,
)

install_exporter = _manager.install
uninstall_exporter = _manager.uninstall
list_exporters = _manager.list
load_exporters = _manager.load_all
load_exporter = _manager.load_module
validate_exporters = _manager.validate_all
get_exporter_module_type = _manager.get_module_type
