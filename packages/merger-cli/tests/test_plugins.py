import pytest
from merger_plugin_api import Parser
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
    return tmp_path

def test_plugin_loader_install(Plugin_dir, mock_config_dir, tmp_path):
    manager = PluginManager(
        plugin_type_name="test",
        base_class=Parser,
        config_key="parsers",
        get_target_dir=lambda: Plugin_dir,
        class_attr="parser_cls",
        key_getter=lambda Plugin: [ext.lower() for ext in getattr(Plugin, "EXTENSIONS")]
    )
    
    Plugin_content = """
from merger_plugin_api import Parser
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

def test_plugin_loader_uninstall(Plugin_dir, mock_config_dir, tmp_path):
    manager = PluginManager(
        plugin_type_name="test",
        base_class=Parser,
        config_key="parsers",
        get_target_dir=lambda: Plugin_dir,
        class_attr="parser_cls",
        key_getter=lambda Plugin: [ext.lower() for ext in getattr(Plugin, "EXTENSIONS")]
    )
    
    Plugin_source = tmp_path / "my_Plugin.py"
    Plugin_source.write_text("parser_cls = None")
    
    from merger_cli.utils.config import get_or_create_config, save_config, PluginEntry
    config = get_or_create_config()
    target_path = Plugin_dir / "abc.py"
    target_path.touch()
    config.parsers["abc"] = PluginEntry(extensions=[".mock"], path=target_path.as_posix(), original_name="my_Plugin.py")
    save_config(config)
    
    assert target_path.exists()
    manager.uninstall("abc")
    assert not target_path.exists()
    assert len(manager.list()) == 0

def test_plugin_loader_load_all_with_broken_Plugin(Plugin_dir, mock_config_dir, tmp_path, caplog):
    manager = PluginManager(
        plugin_type_name="test",
        base_class=Parser,
        config_key="parsers",
        get_target_dir=lambda: Plugin_dir,
        class_attr="parser_cls",
        key_getter=lambda Plugin: [ext.lower() for ext in getattr(Plugin, "EXTENSIONS")]
    )
    
    from merger_cli.utils.config import get_or_create_config, save_config, PluginEntry
    config = get_or_create_config()
    
    broken_path = Plugin_dir / "broken.py"
    broken_path.write_text("invalid python code!")
    config.parsers["broken"] = PluginEntry(extensions=[".broken"], path=broken_path.as_posix(), original_name="broken.py")
    save_config(config)
    
    with caplog.at_level("ERROR"):
        loaded = manager.load_all()
    
    assert len(loaded) == 0
    assert any("Failed to load" in record.message for record in caplog.records)
