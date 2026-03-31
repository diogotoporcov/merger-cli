import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple

from .version import get_version
from ..logging.constants import LOG_COLORS
from rich.console import Console

# Use a separate console to ensure update messages are always displayed 
# even if logging is disabled or set to a higher level.
_update_console = Console(stderr=True)

# Minimum interval between network requests to PyPI (in seconds)
MIN_CHECK_INTERVAL = 60

def log_update(message: str):
    """Print the update message to stderr using rich formatting."""
    color = LOG_COLORS.get("UPDATE", "bold yellow")
    _update_console.print(f"[{color}][UPDATE][/{color}] {message}", markup=True)

def get_latest_version(package_name: str = "merger-cli", etag: Optional[str] = None) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Fetch the latest version of the package from PyPI.
    
    Returns:
        tuple: (latest_version, etag, changed)
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", f"merger-cli/{get_version()} (update-check)")
        if etag:
            req.add_header("If-None-Match", etag)

        with urllib.request.urlopen(req, timeout=5) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                latest = data.get("info", {}).get("version")
                new_etag = response.info().get("ETag")
                return latest, new_etag, True

    except urllib.error.HTTPError as e:
        if e.code == 304:
            return None, etag, False
        
    except Exception:
        pass

    return None, None, False

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

    cached_version = None
    cached_etag = None

    # Try to check cache first
    try:
        if cache_file.exists():
            with open(cache_file, "r") as file:
                cache = json.load(file)
            
            cached_version = cache.get("latest_version")
            cached_etag = cache.get("etag")
            
            # If checked very recently, just use the cached version
            if now - cache.get("last_check", 0) < MIN_CHECK_INTERVAL:
                if cached_version and is_newer_version(cached_version, current_version):
                    display_update_message(current_version, cached_version)
                return

    except Exception:
        pass

    latest_version, new_etag, changed = get_latest_version(etag=cached_etag)
    
    if not changed:
        # If not changed (304), update the check time and keep the old version
        latest_version = cached_version
        new_etag = cached_etag
    
    if not latest_version:
        return

    # Update cache
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as file:
            json.dump({
                "last_check": now,
                "latest_version": latest_version,
                "etag": new_etag
            }, file)

    except Exception:
        pass

    if is_newer_version(latest_version, current_version):
        display_update_message(current_version, latest_version)

def display_update_message(current: str, latest: str):
    """Display the update message using the UPDATE log level."""
    log_update(f"New merger version available: [bold white]{current}[/bold white] -> [bold green]{latest}[/bold green]")
    log_update(f"Update with: [bold magenta]pip install --upgrade merger-cli[/bold magenta] or [bold magenta]pipx upgrade merger-cli[/bold magenta]")
