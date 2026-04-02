from pathlib import Path
from unittest.mock import MagicMock

import pytest
from merger_cli.exceptions import InvalidPlugin, PluginAlreadyInstalled
from merger_plugin_api import Parser as Base
from merger_cli.utils.plugin_loader import PluginManager
from merger_cli.utils.db import PluginRecord


def test_plugin_loader_load_invalid_path():
    mm = PluginManager("test", Base, lambda: Path("."), "cls", lambda _m: [])
    with pytest.raises(FileNotFoundError):
        mm.load_plugin_from_path(Path("non_existent.py"), "test")

def test_plugin_loader_load_directory(tmp_path):
    mm = PluginManager("test", Base, lambda: Path("."), "cls", lambda _m: [])
    dir_path = tmp_path / "somedir"
    dir_path.mkdir()
    with pytest.raises(IsADirectoryError):
        mm.load_plugin_from_path(dir_path, "test")

def test_plugin_loader_get_class_from_plugin():
    mm = PluginManager("test", Base, lambda: Path("."), "test_cls", lambda _m: [])
    
    # Valid Plugin
    class ValidSub(Base): pass
    Plugin = MagicMock()
    Plugin.test_cls = ValidSub
    Plugin.__file__ = "valid.py"
    assert mm.get_class_from_plugin(Plugin) == ValidSub
    
    # Missing attribute
    Plugin_missing = MagicMock()
    del Plugin_missing.test_cls
    with pytest.raises(InvalidPlugin) as exc:
        mm.get_class_from_plugin(Plugin_missing)
    assert "test_cls attribute not provided" in str(exc.value)
    
    # Not a subclass
    class NotSub: pass
    Plugin_not_sub = MagicMock()
    Plugin_not_sub.test_cls = NotSub
    with pytest.raises(InvalidPlugin) as exc:
        mm.get_class_from_plugin(Plugin_not_sub)
    assert f"is not a subclass of {Base.__name__}" in str(exc.value)

@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger_cli.utils.config.get_merger_dir", lambda: tmp_path)
    return tmp_path

def test_plugin_loader_install_uninstall(tmp_path, mock_config_dir, monkeypatch):
    # Mock uv_install and uv_purge
    monkeypatch.setattr("merger_cli.utils.plugin_loader.uv_install", lambda *args, **kwargs: None)
    monkeypatch.setattr("merger_cli.utils.plugin_loader.uv_purge", lambda *args, **kwargs: None)

    target_dir = mock_config_dir / "test_Plugins"
    mm = PluginManager(
        "test", 
        Base, 
        lambda: target_dir, 
        "test_cls", 
        lambda _m: ["key"]
    )
    
    Plugin_content = """
from merger_plugin_api import Parser
class MyPlugin(Parser):
    EXTENSIONS = [".test"]
    REQUIREMENTS = ["pkgA"]
test_cls = MyPlugin
"""
    plugin_path = tmp_path / "my_mod.py"
    plugin_path.write_text(Plugin_content)
    
    # Install
    mm.install(plugin_path)
    
    # Verify installation
    installed = mm.list()
    assert len(installed) == 1
    plugin_id = installed[0].id
    entry = installed[0]
    assert entry.original_name == "my_mod.py"
    assert Path(entry.path).exists()
    assert target_dir.exists()
    
    # Already installed
    with pytest.raises(PluginAlreadyInstalled):
        mm.install(plugin_path)
    
    # Load all
    loaded = mm.load_all()
    assert "key" in loaded
    assert loaded["key"].__name__ == "MyPlugin"
    
    # Uninstall
    mm.uninstall(plugin_id)
    assert len(mm.list()) == 0
    assert not Path(entry.path).exists()

def test_plugin_loader_uninstall_all(tmp_path, mock_config_dir, monkeypatch):
    # Mock uv_purge
    monkeypatch.setattr("merger_cli.utils.plugin_loader.uv_purge", lambda *args, **kwargs: None)

    target_dir = mock_config_dir / "test_Plugins"
    mm = PluginManager("test", Base, lambda: target_dir, "test_cls", lambda _m: [])
    
    # Create two dummy Plugins in target_dir and register them in DB
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
    mm = PluginManager("test_type", Base, lambda: Path("."), "test_cls", lambda _m: [])
    
    Plugin_content = """
from merger_plugin_api import Parser
class MyPlugin(Parser): pass
test_cls = MyPlugin
"""
    plugin_path = tmp_path / "type_mod.py"
    plugin_path.write_text(Plugin_content)
    
    assert mm.get_plugin_type(plugin_path) == "test_type"
    
    # Not a Plugin
    other_path = tmp_path / "other.py"
    other_path.write_text("test_cls = 1")
    assert mm.get_plugin_type(other_path) == "unknown"
