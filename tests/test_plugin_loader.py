from pathlib import Path
from unittest.mock import MagicMock

import pytest
from merger.exceptions import InvalidPlugin, PluginAlreadyInstalled
from merger.parsing.base import Parser as Base
from merger.utils.db import PluginRecord
from merger.utils.plugin_loader import PluginManager


def test_plugin_loader_load_invalid_path():
    mm = PluginManager("test", Base, lambda: Path("."), lambda _m, _c: [])
    with pytest.raises(FileNotFoundError):
        mm.load_plugin_from_path(Path("non_existent.py"), "test")

def test_plugin_loader_load_directory(tmp_path):
    mm = PluginManager("test", Base, lambda: Path("."), lambda _m, _c: [])
    dir_path = tmp_path / "somedir"
    dir_path.mkdir()
    with pytest.raises(IsADirectoryError):
        mm.load_plugin_from_path(dir_path, "test")

def test_plugin_loader_get_class_from_plugin():
    mm = PluginManager("test", Base, lambda: Path("."), lambda _m, _c: [])
    
    # Valid Plugin
    class ValidSub(Base):
        @classmethod
        def validate(cls, b, p): return True
        @classmethod
        def parse(cls, b, p): return ""

    plugin = MagicMock()
    plugin.ValidSub = ValidSub
    plugin.__file__ = "valid.py"
    assert mm.get_class_from_plugin(plugin) == ValidSub
    
    # No subclass
    class NotSub: pass
    plugin_not_sub = MagicMock()
    plugin_not_sub.NotSub = NotSub
    with pytest.raises(InvalidPlugin) as exc:
        mm.get_class_from_plugin(plugin_not_sub)
    assert f"No subclass of {Base.__name__} found" in str(exc.value)

@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger.utils.config.get_merger_dir", lambda: tmp_path)
    return tmp_path

def test_plugin_loader_install_uninstall(tmp_path, mock_config_dir, monkeypatch):

    target_dir = mock_config_dir / "test_Plugins"
    mm = PluginManager(
        "test", 
        Base, 
        lambda: target_dir, 
        lambda _m, _c: ["key"]
    )
    
    Plugin_content = f"""
from {Base.__module__} import {Base.__name__}
class MyPlugin({Base.__name__}):
    EXTENSIONS = [".test"]
    @classmethod
    def validate(cls, b, p): return True
    @classmethod
    def parse(cls, b, p): return ""
"""
    plugin_path = tmp_path / "my_mod.py"
    plugin_path.write_text(Plugin_content)
    
    mm.install(plugin_path)
    
    installed = mm.list()
    assert len(installed) == 1
    plugin_id = installed[0].id
    entry = installed[0]
    assert entry.original_name == "my_mod.py"
    assert Path(entry.path).exists()
    assert target_dir.exists()
    
    with pytest.raises(PluginAlreadyInstalled):
        mm.install(plugin_path)
    
    loaded = mm.load_all()
    assert "key" in loaded
    assert loaded["key"].__name__ == "MyPlugin"
    
    mm.uninstall(plugin_id)
    assert len(mm.list()) == 0
    assert not Path(entry.path).exists()

def test_plugin_loader_uninstall_all(tmp_path, mock_config_dir, monkeypatch):

    target_dir = mock_config_dir / "test_Plugins"
    mm = PluginManager("test", Base, lambda: target_dir, lambda _m, _c: [])
    
    target_dir.mkdir()
    p1_path = target_dir / "m1.py"
    p2_path = target_dir / "m2.py"
    p1_path.touch()
    p2_path.touch()
    
    mm.db.add_plugin(PluginRecord(id="id1", name="m1", type="test", path=str(p1_path), original_name="m1.py", extensions=[]))
    mm.db.add_plugin(PluginRecord(id="id2", name="m2", type="test", path=str(p2_path), original_name="m2.py", extensions=[]))
    
    assert len(mm.list()) == 2
    
    mm.uninstall("*")
    assert len(mm.list()) == 0
    assert not p1_path.exists()
    assert not p2_path.exists()

def test_plugin_loader_get_plugin_type(tmp_path):
    mm = PluginManager("test_type", Base, lambda: Path("."), lambda _m, _c: [])
    
    Plugin_content = f"""
from {Base.__module__} import {Base.__name__}
class MyPlugin({Base.__name__}):
    @classmethod
    def validate(cls, b, p): return True
    @classmethod
    def parse(cls, b, p): return ""
"""
    plugin_path = tmp_path / "type_mod.py"
    plugin_path.write_text(Plugin_content)
    
    assert mm.get_plugin_type(plugin_path) == "test_type"
    
    # Not a Plugin
    other_path = tmp_path / "other.py"
    other_path.write_text("test_cls = 1")
    assert mm.get_plugin_type(other_path) == "unknown"
