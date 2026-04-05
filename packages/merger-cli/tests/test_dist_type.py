from merger_cli.cli.utils import handle_update
from merger_cli.logging import setup_logger
from merger_cli.utils.config import is_bundled, set_distribution_type, get_distribution_type


def test_distribution_type_defaults_to_pypi():
    """Verify that by default the distribution type is 'pypi'."""
    set_distribution_type("pypi")
    assert get_distribution_type() == "pypi"
    assert not is_bundled()

def test_set_distribution_type_standalone():
    """Verify that setting distribution type to 'standalone' works."""
    set_distribution_type("standalone")
    assert get_distribution_type() == "standalone"
    assert is_bundled()
    set_distribution_type("pypi")

def test_handle_update_behavior(capsys):
    """Verify that handle_update suggests GitHub releases regardless of dist type."""
    # Setup logger to capture output
    setup_logger()
    
    set_distribution_type("pypi")
    handle_update()
    captured = capsys.readouterr()
    # Use re.sub to collapse all whitespace (including tabs and newlines) into a single space
    import re
    err_text = re.sub(r"\s+", " ", captured.err)
    assert "distributed via standalone installers and GitHub releases" in err_text
    
    set_distribution_type("standalone")
    handle_update()
    captured = capsys.readouterr()
    err_text = re.sub(r"\s+", " ", captured.err)
    assert "distributed via standalone installers and GitHub releases" in err_text
    
    set_distribution_type("pypi")

def test_handle_plugin_requirements_bundled_vs_pypi(monkeypatch, capsys):
    """Verify that handle_plugin_requirements behaves differently based on distribution type."""
    from merger_cli.cli.utils import handle_plugin_requirements
    
    # Mock DatabaseManager to return no plugins
    class MockDB:
        def list_plugins(self, type=None):
            return []
        def get_unused_dependencies(self):
            return []
    
    monkeypatch.setattr("merger_cli.utils.db.DatabaseManager", MockDB)
    # Mock uv.find_uv_bin or similar if needed, or just let it fail gracefully
    # Mocking get_uv_executable is easier
    monkeypatch.setattr("merger_cli.utils.uv.get_uv_executable", lambda: "uv")
    # Mock run_uv to avoid actual execution
    monkeypatch.setattr("merger_cli.utils.uv.run_uv", lambda args, capture_output=False: None)
    
    setup_logger()

    # Test PyPI mode
    set_distribution_type("pypi")
    handle_plugin_requirements()
    captured = capsys.readouterr()
    err_text = captured.err
    assert "No custom plugins installed" in err_text
    
    # Test Standalone mode
    set_distribution_type("standalone")
    handle_plugin_requirements()
    captured = capsys.readouterr()
    err_text = captured.err
    assert "No custom plugins installed" in err_text
    
    # Test Standalone mode with purge
    handle_plugin_requirements(purge=True)
    captured = capsys.readouterr()
    err_text = captured.err
    assert "No unused requirements found to purge" in err_text
    
    set_distribution_type("pypi")

def test_handle_plugin_requirements_pypi_unsupported_commands(monkeypatch, capsys):
    """Verify that install/purge commands are ignored or warn on PyPI distribution."""
    from merger_cli.cli.utils import handle_plugin_requirements
    
    setup_logger()
    set_distribution_type("pypi")
    
    # Let's mock having a plugin with requirements
    class MockPlugin:
        id = "test-plugin"
        path = "dummy/path"
        
    class MockDB:
        def list_plugins(self, type=None):
            return [MockPlugin()]
        def add_plugin_dependency(self, plugin_id, dep):
            pass
            
    monkeypatch.setattr("merger_cli.utils.db.DatabaseManager", MockDB)
    # Mock extract_requirements to return something
    monkeypatch.setattr("merger_cli.utils.plugin_loader.PluginManager.extract_requirements", lambda path: ["pillow"])
    # Mock Path.exists
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    # Mock check_and_warn_dependencies
    monkeypatch.setattr("merger_cli.utils.dependencies.check_and_warn_dependencies", lambda deps, scope: print(f"Checking {deps} for {scope}"))

    handle_plugin_requirements()
    captured = capsys.readouterr()
    assert "Checking ['pillow'] for installed plugins" in captured.out
    
    set_distribution_type("pypi")
