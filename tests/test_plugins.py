import pytest
from merger_cli.api import Parser
from merger_cli.utils.db import PluginRecord
from merger_cli.utils.plugin_loader import PluginManager


class MockParser(Parser):
    EXTENSIONS = [".mock"]
    @classmethod
    def validate(cls, file_bytes, file_path): return True
    @classmethod
    def parse(cls, file_bytes, file_path): return "mock content"

@pytest.fixture
def Plugin_dir(tmp_path):
    d = tmp_path / "parsers"
    d.mkdir()
    return d

@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger_cli.utils.config.get_merger_dir", lambda: tmp_path)
    # Clear the lazy DB cache in the managers if they were loaded
    try:
        from merger_cli.parsing.registry import _manager as pm
        pm._db = None
    except ImportError:
        pass
    try:
        from merger_cli.exporters.registry import _manager as em
        em._db = None
    except ImportError:
        pass
    return tmp_path

def test_plugin_loader_install(Plugin_dir, mock_config_dir, tmp_path, monkeypatch):

    manager = PluginManager(
        plugin_type_name="test",
        base_class=Parser,
        get_target_dir=lambda: Plugin_dir,
        class_attr="parser_cls",
        key_getter=lambda Plugin: [ext.lower() for ext in getattr(Plugin, "EXTENSIONS")]
    )
    
    Plugin_content = """
from merger_cli.api import Parser
EXTENSIONS = [".mock"]
class MockParser(Parser):
    @classmethod
    def validate(cls, file_bytes, file_path): return True
    @classmethod
    def parse(cls, file_bytes, file_path): return "mocked"
parser_cls = MockParser
"""
    Plugin_source = tmp_path / "my_Plugin.py"
    Plugin_source.write_text(Plugin_content)
    
    manager.install(Plugin_source)
    
    assert len(list(Plugin_dir.glob("*.py"))) == 1
    config_Plugins = manager.list()
    assert len(config_Plugins) == 1
    
    loaded = manager.load_all()
    assert ".mock" in loaded
    assert loaded[".mock"].parse(b"", tmp_path) == "mocked"

def test_plugin_loader_uninstall(Plugin_dir, mock_config_dir, tmp_path, monkeypatch):

    manager = PluginManager(
        plugin_type_name="test",
        base_class=Parser,
        get_target_dir=lambda: Plugin_dir,
        class_attr="parser_cls",
        key_getter=lambda Plugin: [ext.lower() for ext in getattr(Plugin, "EXTENSIONS")]
    )
    
    Plugin_source = tmp_path / "my_Plugin.py"
    Plugin_source.write_text("parser_cls = None")
    
    target_path = Plugin_dir / "abc.py"
    target_path.touch()
    
    manager.db.add_plugin(PluginRecord(id="abc", name="my_Plugin", type="test", path=str(target_path), original_name="my_Plugin.py", extensions=[".mock"]))
    
    assert target_path.exists()
    manager.uninstall("abc")
    assert not target_path.exists()
    assert len(manager.list()) == 0

def test_plugin_loader_load_all_with_broken_Plugin(Plugin_dir, mock_config_dir, tmp_path, caplog):
    manager = PluginManager(
        plugin_type_name="test",
        base_class=Parser,
        get_target_dir=lambda: Plugin_dir,
        class_attr="parser_cls",
        key_getter=lambda Plugin: [ext.lower() for ext in getattr(Plugin, "EXTENSIONS")]
    )
    
    broken_path = Plugin_dir / "broken.py"
    broken_path.write_text("invalid python code!")
    manager.db.add_plugin(PluginRecord(id="broken", name="broken", type="test", path=str(broken_path), original_name="broken.py", extensions=[".broken"]))
    
    with caplog.at_level("ERROR"):
        loaded = manager.load_all()
    
    assert len(loaded) == 0
    assert any("Failed to load" in record.message for record in caplog.records)
