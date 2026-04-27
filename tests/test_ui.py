import json
import os
import time
from pathlib import Path

import merger.utils.update
from rich.console import Console


def mock_get_version():
    return "1.0.0"

merger.utils.update.get_version = mock_get_version

# Force cache to say there is a newer version
cache_dir = Path.home() / ".merger"
cache_file = cache_dir / "update_check.json"
cache_dir.mkdir(parents=True, exist_ok=True)

old_cache = None
if cache_file.exists():
    old_cache = cache_file.read_text()

try:
    print("--- Test 1: Standard Update Display ---")
    with open(cache_file, "w") as f:
        json.dump({
            "last_check": time.time(),
            "latest_version": "2.0.0",
            "etag": "some-etag"
        }, f)

    merger.utils.update.check_for_updates()
    merger.utils.update.finalize_update_check()

    print("\n--- Test 2: CI Environment (Should skip) ---")
    os.environ["CI"] = "true"
    # The pending message must be reset if it was set
    merger.utils.update._pending_message = None 
    
    merger.utils.update.check_for_updates()
    merger.utils.update.finalize_update_check()
    del os.environ["CI"]

    print("\n--- Test 3: Non-TTY (Should skip display) ---")
    if merger.utils.update._update_console is None:
        merger.utils.update._update_console = Console(stderr=True)
    original_is_terminal = merger.utils.update._update_console.is_terminal
    merger.utils.update._update_console = Console(force_terminal=False)
    
    # Reload pending message from cache
    merger.utils.update.check_for_updates()
    merger.utils.update.finalize_update_check()
    
finally:
    if old_cache is not None:
        cache_file.write_text(old_cache)
    else:
        cache_file.unlink(missing_ok=True)
