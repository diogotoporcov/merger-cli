import json

import pytest
from merger_cli.utils.config import get_or_create_config, save_config, ConfigModel, PluginEntry


@pytest.fixture
def mock_merger_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("merger_cli.utils.config.get_merger_dir", lambda: tmp_path)
    return tmp_path

def test_config_creation(mock_merger_dir):
    config = get_or_create_config()
    assert isinstance(config, ConfigModel)
    assert config.version == 1
    assert config.parsers == {}
    assert config.exporters == {}
    
    config_path = mock_merger_dir / "config.json"
    assert config_path.exists()

def test_config_save_load(mock_merger_dir):
    config = get_or_create_config()
    entry = PluginEntry(extensions=[".pdf"], path="/fake/path", original_name="pdf.py")
    config.parsers["test"] = entry
    save_config(config)
    
    # Reload
    new_config = get_or_create_config()
    assert "test" in new_config.parsers
    assert new_config.parsers["test"].extensions == [".pdf"]

def test_config_migration_v0_to_v1(mock_merger_dir):
    # Create a v0 config (no version, just Plugins)
    config_path = mock_merger_dir / "config.json"
    mock_merger_dir.mkdir(parents=True, exist_ok=True)
    
    old_data = {
        "parsers": {
            "test": {
                "extensions": [".pdf"],
                "path": "/fake/path",
                "original_name": "pdf.py"
            }
        }
    }
    with open(config_path, "w") as f:
        json.dump(old_data, f)
        
    # Load and migrate
    config = get_or_create_config()
    assert config.version == 1
    assert "test" in config.parsers
    assert "exporters" in config.model_dump()
    
    # Verify file was updated
    with open(config_path, "r") as f:
        updated_data = json.load(f)
        assert updated_data["version"] == 1
        assert "exporters" in updated_data
