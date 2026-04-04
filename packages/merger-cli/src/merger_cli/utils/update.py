import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from typing import Optional, Tuple

from .config import get_merger_dir, is_bundled
from .version import get_version
from ..logging.constants import LOG_COLORS

# Minimum interval between network requests to PyPI (in seconds)
MIN_CHECK_INTERVAL = 3600

# Globals for asynchronous update check
_pending_message: Optional[str] = None
_update_thread: Optional[threading.Thread] = None


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

        with urllib.request.urlopen(req, timeout=10) as response:
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

def get_latest_github_version(repo_url: str = "https://github.com/diogotoporcov/merger-cli") -> Optional[str]:
    """Fetch the latest release version from GitHub."""
    parts = repo_url.rstrip("/").split("/")
    if len(parts) < 2:
        return None
    owner, repo = parts[-2], parts[-1]
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", f"merger-cli/{get_version()} (update-check)")
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.getcode() == 200:
                data = json.loads(response.read().decode())
                tag = data.get("tag_name", "")
                # Remove 'v' prefix if present
                if tag.startswith("v"):
                    tag = tag[1:]
                return tag
    except Exception:
        pass
    return None

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

def is_ci_environment() -> bool:
    """
    Detect if the code is running in a CI/automated environment.
    Most major CLIs skip update checks in CI to avoid noise and network usage.
    """
    ci_vars = [
        "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS", "TRAVIS", 
        "CIRCLECI", "GITLAB_CI", "JENKINS_URL", "BUILD_NUMBER",
        "RUN_ID"
    ]
    return any(os.environ.get(var) for var in ci_vars)

def check_for_updates():
    """
    Start the update check process. 
    It will check cache first, and if needed, start a background thread for network check.
    """
    if (os.environ.get("MERGER_SKIP_UPDATE_CHECK") or 
        os.environ.get("NO_UPDATE_CHECK") or 
        is_ci_environment()):
        return

    current_version = get_version()
    if current_version == "unknown":
        return

    cache_dir = get_merger_dir()
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
    """Background worker to check for updates."""
    # Check PyPI (if it was installed via pip previously)
    latest_version, new_etag, changed = get_latest_version(etag=cached_etag)
    
    # Always check GitHub Releases for the CLI tool, as it is the primary distribution method
    github_latest = get_latest_github_version()
    if github_latest and (not latest_version or is_newer_version(github_latest, latest_version)):
        latest_version = github_latest
        changed = True
        new_etag = None # ETag doesn't apply to GitHub check this way

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
    
    if is_bundled():
        update_cmd = "Download new version: [bold magenta]https://github.com/diogotoporcov/merger-cli/releases[/bold magenta]"
    else:
        # Since merger-cli is not on PyPI anymore, suggest checking the releases page
        update_cmd = "Check for updates at: [bold magenta]https://github.com/diogotoporcov/merger-cli/releases[/bold magenta]"

    _pending_message = (
        f"New Merger CLI version available: [bold white]{current}[/bold white] -> [bold green]{latest}[/bold green]\n"
        f"{update_cmd}"
    )

_update_console = None


def finalize_update_check():
    """Display the update message if one is pending. Call this at the end of the program."""
    global _pending_message, _update_console
    if _pending_message:
        from rich.console import Console
        from rich.panel import Panel

        if _update_console is None:
            _update_console = Console(stderr=True)

        # Only show update notifications in interactive terminals
        if _update_console.is_terminal:
            color = LOG_COLORS.get("UPDATE", "yellow")
            _update_console.print()  # Add a newline for better spacing
            _update_console.print(Panel(
                _pending_message,
                title=f"[bold {color}]Update Available[/bold {color}]",
                border_style=color,
                expand=False,
                padding=(0, 2)
            ))
            
        _pending_message = None
