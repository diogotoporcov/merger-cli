import json
import logging
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Optional

from .version import get_version
from ..logging.constants import LOG_COLORS, UPDATE_LEVEL
from rich.console import Console

# Use a separate console to ensure update messages are always displayed 
# even if logging is disabled or set to a higher level.
_update_console = Console(stderr=True)

def log_update(message: str):
    """Print the update message to stderr using rich formatting."""
    color = LOG_COLORS.get("UPDATE", "bold yellow")
    _update_console.print(f"[{color}][UPDATE][/{color}] {message}", markup=True)

def get_latest_version(package_name: str = "merger-cli") -> Optional[str]:
    """Fetch the latest version of the package from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                return data.get("info", {}).get("version")

    except Exception:
        pass

    return None

def is_newer_version(latest: str, current: str) -> bool:
    """Compare two version strings."""
    try:
        def parse_version(v):
            return [
                int(part)
                for part in re.findall(r'\d+', v)
            ]
        
        l_parts = parse_version(latest)
        c_parts = parse_version(current)
        
        return l_parts > c_parts

    except Exception:
        return latest > current

def check_for_updates():
    """Check for updates and display a message if a new version is available."""
    if os.environ.get("MERGER_SKIP_UPDATE_CHECK"):
        return

    current_version = get_version()
    if current_version == "unknown":
        return

    # Cache directory
    cache_dir = Path.home() / ".merger"
    cache_file = cache_dir / "update_check.json"
    
    now = time.time()
    cache_duration = 3600

    # Try to check cache first
    try:
        if cache_file.exists():
            with open(cache_file, "r") as file:
                cache = json.load(file)
            
            last_check = cache.get("last_check", 0)
            latest_version = cache.get("latest_version")
            
            # If checked recently, just use the cached version
            if now - last_check < cache_duration:
                if latest_version and is_newer_version(latest_version, current_version):
                    display_update_message(current_version, latest_version)
                return

    except Exception:
        pass

    # Perform fresh check
    latest_version = get_latest_version()
    if not latest_version:
        return

    # Update cache
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as file:
            json.dump({
                "last_check": now,
                "latest_version": latest_version
            }, file)

    except Exception:
        pass

    if is_newer_version(latest_version, current_version):
        display_update_message(current_version, latest_version)

def display_update_message(current: str, latest: str):
    """Display the update message using the UPDATE log level."""
    log_update(f"New merger version available: [bold white]{current}[/bold white] -> [bold green]{latest}[/bold green]")
    log_update(f"Update with: [bold magenta]pip install --upgrade merger-cli[/bold magenta] or [bold magenta]pipx upgrade merger-cli[/bold magenta]")
