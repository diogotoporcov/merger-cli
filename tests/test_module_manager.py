from pathlib import Path
from unittest.mock import MagicMock

import pytest
from merger_cli.exceptions import InvalidModule, ModuleAlreadyInstalled
from merger_api import Parser as Base
from merger_cli.utils.module_manager import ModuleManager


def test_module_manager_load_invalid_path():
    mm = ModuleManager("test", Base, "modules", lambda: Path("."), "cls", lambda _m: [])
    with pytest.raises(FileNotFoundError):
        mm.load_module_from_path(Path("non_existent.py"), "test")

def test_module_manager_load_directory(tmp_path):
    mm = ModuleManager("test", Base, "modules", lambda: Path("."), "cls", lambda _m: [])
    dir_path = tmp_path / "somedir"
    dir_path.mkdir()
    with pytest.raises(IsADirectoryError):
        mm.load_module_from_path(dir_path, "test")

def test_module_manager_get_class_from_module():
    mm = ModuleManager("test", Base, "modules", lambda: Path("."), "test_cls", lambda _m: [])
    
    # Valid module
    class ValidSub(Base): pass
    module = MagicMock()
    module.test_cls = ValidSub
    module.__file__ = "valid.py"
    assert mm.get_class_from_module(module) == ValidSub
    
    # Missing attribute
    module_missing = MagicMock()
    del module_missing.test_cls
    with pytest.raises(InvalidModule) as exc:
        mm.get_class_from_module(module_missing)
    assert "test_cls attribute not provided" in str(exc.value)
    
    # Not a subclass
    class NotSub: pass
    module_not_sub = MagicMock()
    module_not_sub.test_cls = NotSub
    with pytest.raises(InvalidModule) as exc:
        mm.get_class_from_module(module_not_sub)
    assert f"is not a subclass of {Base.__name__}" in str(exc.value)

@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger_cli.utils.config.get_merger_dir", lambda: tmp_path)
    return tmp_path

def test_module_manager_install_uninstall(tmp_path, mock_config_dir):
    target_dir = mock_config_dir / "test_modules"
    mm = ModuleManager(
        "test", 
        Base, 
        "modules", 
        lambda: target_dir, 
        "test_cls", 
        lambda _m: ["key"]
    )
    
    module_content = """
from merger_api import Parser
class MyModule(Parser):
    EXTENSIONS = [".test"]
test_cls = MyModule
"""
    module_path = tmp_path / "my_mod.py"
    module_path.write_text(module_content)
    
    # Install
    mm.install(module_path)
    
    # Verify installation
    installed = mm.list()
    assert len(installed) == 1
    module_id = list(installed.keys())[0]
    entry = installed[module_id]
    assert entry.original_name == "my_mod.py"
    assert Path(entry.path).exists()
    assert target_dir.exists()
    
    # Already installed
    with pytest.raises(ModuleAlreadyInstalled):
        mm.install(module_path)
    
    # Load all
    loaded = mm.load_all()
    assert "key" in loaded
    assert loaded["key"].__name__ == "MyModule"
    
    # Uninstall
    mm.uninstall(module_id)
    assert len(mm.list()) == 0
    assert not Path(entry.path).exists()

def test_module_manager_uninstall_all(tmp_path, mock_config_dir):
    target_dir = mock_config_dir / "test_modules"
    mm = ModuleManager("test", Base, "modules", lambda: target_dir, "test_cls", lambda _m: [])
    
    # Create two dummy modules in target_dir and register them in config
    target_dir.mkdir()
    (target_dir / "m1.py").touch()
    (target_dir / "m2.py").touch()
    
    from merger_cli.utils.config import get_or_create_config, save_config, ModuleEntry
    config = get_or_create_config()
    config.modules["id1"] = ModuleEntry(extensions=[], path=(target_dir / "m1.py").as_posix(), original_name="m1.py")
    config.modules["id2"] = ModuleEntry(extensions=[], path=(target_dir / "m2.py").as_posix(), original_name="m2.py")
    save_config(config)
    
    assert len(mm.list()) == 2
    
    mm.uninstall("*")
    assert len(mm.list()) == 0
    assert not (target_dir / "m1.py").exists()
    assert not (target_dir / "m2.py").exists()

def test_module_manager_get_module_type(tmp_path):
    mm = ModuleManager("test_type", Base, "modules", lambda: Path("."), "test_cls", lambda _m: [])
    
    module_content = """
from merger_api import Parser
class MyModule(Parser): pass
test_cls = MyModule
"""
    module_path = tmp_path / "type_mod.py"
    module_path.write_text(module_content)
    
    assert mm.get_module_type(module_path) == "test_type"
    
    # Not a module
    other_path = tmp_path / "other.py"
    other_path.write_text("test_cls = 1")
    assert mm.get_module_type(other_path) == "unknown"
