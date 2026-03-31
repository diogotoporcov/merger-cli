import pytest
from merger.parsing.parser import Parser
from merger.utils.module_manager import ModuleManager


class MockParser(Parser):
    EXTENSIONS = [".mock"]
    @classmethod
    def validate(cls, file_bytes, file_path): return True
    @classmethod
    def parse(cls, file_bytes, file_path): return "mock content"

@pytest.fixture
def module_dir(tmp_path):
    d = tmp_path / "modules"
    d.mkdir()
    return d

@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger.utils.config.get_merger_dir", lambda: tmp_path)
    return tmp_path

def test_module_manager_install(module_dir, mock_config_dir, tmp_path):
    manager = ModuleManager(
        module_type_name="test",
        base_class=Parser,
        config_key="modules",
        get_target_dir=lambda: module_dir,
        class_attr="parser_cls",
        key_getter=lambda cls: [ext.lower() for ext in getattr(cls, "EXTENSIONS")]
    )
    
    module_content = """
from merger.parsing.parser import Parser
class MockParser(Parser):
    EXTENSIONS = [".mock"]
    @classmethod
    def validate(cls, file_bytes, file_path): return True
    @classmethod
    def parse(cls, file_bytes, file_path): return "mocked"
parser_cls = MockParser
"""
    module_source = tmp_path / "my_module.py"
    module_source.write_text(module_content)
    
    manager.install(module_source)
    
    assert len(list(module_dir.glob("*.py"))) == 1
    config_modules = manager.list()
    assert len(config_modules) == 1
    
    loaded = manager.load_all()
    assert ".mock" in loaded
    assert loaded[".mock"].parse(b"", tmp_path) == "mocked"

def test_module_manager_uninstall(module_dir, mock_config_dir, tmp_path):
    manager = ModuleManager(
        module_type_name="test",
        base_class=Parser,
        config_key="modules",
        get_target_dir=lambda: module_dir,
        class_attr="parser_cls",
        key_getter=lambda cls: [ext.lower() for ext in getattr(cls, "EXTENSIONS")]
    )
    
    module_source = tmp_path / "my_module.py"
    module_source.write_text("parser_cls = None")
    
    from merger.utils.config import get_or_create_config, save_config, ModuleEntry
    config = get_or_create_config()
    target_path = module_dir / "abc.py"
    target_path.touch()
    config.modules["abc"] = ModuleEntry(extensions=[".mock"], path=target_path.as_posix(), original_name="my_module.py")
    save_config(config)
    
    assert target_path.exists()
    manager.uninstall("abc")
    assert not target_path.exists()
    assert len(manager.list()) == 0

def test_module_manager_load_all_with_broken_module(module_dir, mock_config_dir, tmp_path, caplog):
    manager = ModuleManager(
        module_type_name="test",
        base_class=Parser,
        config_key="modules",
        get_target_dir=lambda: module_dir,
        class_attr="parser_cls",
        key_getter=lambda cls: [ext.lower() for ext in getattr(cls, "EXTENSIONS")]
    )
    
    from merger.utils.config import get_or_create_config, save_config, ModuleEntry
    config = get_or_create_config()
    
    broken_path = module_dir / "broken.py"
    broken_path.write_text("invalid python code!")
    config.modules["broken"] = ModuleEntry(extensions=[".broken"], path=broken_path.as_posix(), original_name="broken.py")
    save_config(config)
    
    with caplog.at_level("ERROR"):
        loaded = manager.load_all()
    
    assert len(loaded) == 0
    assert any("Failed to load" in record.message for record in caplog.records)
