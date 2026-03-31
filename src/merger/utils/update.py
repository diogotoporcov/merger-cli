import json
import os
import re
import time
import urllib.request
import urllib.error
import threading
from pathlib import Path
from typing import Optional, Tuple

from .version import get_version
from ..logging.constants import LOG_COLORS
from rich.console import Console

# Use a separate console to ensure update messages are always displayed 
# even if logging is disabled or set to a higher level.
_update_console = Console(stderr=True)

# Minimum interval between network requests to PyPI (in seconds)
MIN_CHECK_INTERVAL = 3600

# Globals for asynchronous update check
_pending_message: Optional[str] = None
_update_thread: Optional[threading.Thread] = None

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
    """Compare two version strings with support for pre-releases and post-releases."""
    try:
        from packaging import version
        return version.parse(latest) > version.parse(current)

    except (ImportError, Exception):
        def parse(v):
            parts = re.split(r'([a-zA-Z]+|\d+)', v)
            result = []
            for p in parts:
                p = p.strip('-._ ')
                if not p:
                    continue
                if p.isdigit():
                    result.append(int(p))

                else:
                    p = p.lower()
                    if p in ('a', 'alpha'):
                        result.append(-3)
                    elif p in ('b', 'beta'):
                        result.append(-2)
                    elif p in ('rc', 'c', 'pre', 'preview'):
                        result.append(-1)
                    elif p in ('post', 'r', 'rev'):
                        result.append(1)

            return result

        l_parts = parse(latest)
        c_parts = parse(current)
        
        for i in range(min(len(l_parts), len(c_parts))):
            if l_parts[i] > c_parts[i]: return True
            if l_parts[i] < c_parts[i]: return False
        
        if len(l_parts) > len(c_parts):
            return l_parts[len(c_parts)] > 0

        if len(c_parts) > len(l_parts):
            return c_parts[len(l_parts)] < 0
            
        return False

def check_for_updates():
    """
    Start the update check process. 
    It will check cache first, and if needed, start a background thread for network check.
    """
    if os.environ.get("MERGER_SKIP_UPDATE_CHECK"):
        return

    current_version = get_version()
    if current_version == "unknown":
        return

    cache_dir = Path.home() / ".merger"
    cache_file = cache_dir / "update_check.json"
    
    now = time.time()
    
    cached_version = None
    cached_etag = None

    try:
        if cache_file.exists():
            with open(cache_file, "r") as file:
                cache = json.load(file)
            
            cached_version = cache.get("latest_version")
            cached_etag = cache.get("etag")
            last_check = cache.get("last_check", 0)
            
            if cached_version and is_newer_version(cached_version, current_version):
                set_pending_update_message(current_version, cached_version)

            if now - last_check < MIN_CHECK_INTERVAL:
                return

    except Exception:
        pass

    global _update_thread
    _update_thread = threading.Thread(
        target=_update_worker, 
        args=(current_version, cache_file, cache_dir, cached_version, cached_etag),
        daemon=True
    )
    _update_thread.start()

def _update_worker(current_version, cache_file, cache_dir, cached_version, cached_etag):
    """Background worker to check PyPI for updates."""
    latest_version, new_etag, changed = get_latest_version(etag=cached_etag)
    
    if not changed:
        latest_version = cached_version
        new_etag = cached_etag
    
    if not latest_version:
        return

    # Update cache
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as file:
            json.dump({
                "last_check": time.time(),
                "latest_version": latest_version,
                "etag": new_etag
            }, file)
    except Exception:
        pass

    if is_newer_version(latest_version, current_version):
        set_pending_update_message(current_version, latest_version)

def set_pending_update_message(current: str, latest: str):
    """Prepare the update message to be displayed later."""
    global _pending_message
    _pending_message = (
        f"New merger version available: [bold white]{current}[/bold white] -> [bold green]{latest}[/bold green]\n"
        f"Update with: [bold magenta]pip install --upgrade merger-cli[/bold magenta] or [bold magenta]pipx upgrade merger-cli[/bold magenta]"
    )

def finalize_update_check():
    """Display the update message if one is pending. Call this at the end of the program."""
    global _pending_message
    if _pending_message:
        for line in _pending_message.split("\n"):
            log_update(line)
            
        _pending_message = None
