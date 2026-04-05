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

def test_handle_plugin_update_bundled_vs_pypi(monkeypatch, capsys):
    """Verify that handle_plugin_update behaves differently based on distribution type."""
    from merger_cli.cli.utils import handle_plugin_update
    
    # Mock DatabaseManager to return no plugins
    class MockDB:
        def list_plugins(self):
            return []
    
    monkeypatch.setattr("merger_cli.utils.db.DatabaseManager", MockDB)
    setup_logger()

    # Test PyPI mode
    set_distribution_type("pypi")
    handle_plugin_update()
    captured = capsys.readouterr()
    import re
    err_text = re.sub(r"\s+", " ", captured.err)
    assert "No custom plugins installed to check for dependency updates." in err_text
    
    # Test Standalone mode
    set_distribution_type("standalone")
    handle_plugin_update()
    captured = capsys.readouterr()
    err_text = re.sub(r"\s+", " ", captured.err)
    assert "No custom plugins installed to check for dependency updates." in err_text
    
    set_distribution_type("pypi")
