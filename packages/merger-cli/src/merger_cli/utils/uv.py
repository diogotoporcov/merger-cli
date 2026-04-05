import subprocess
from pathlib import Path
from typing import List, Optional

from .config import get_or_create_site_packages_dir
from ..logging import logger


def get_uv_executable() -> str:
    """Finds the uv executable. Fallbacks to using 'uv' if not found in common places."""
    try:
        import uv
        return uv.find_uv_bin()
    except (ImportError, AttributeError):
        pass

    try:
        subprocess.run(["uv", "--version"], capture_output=True, check=True)
        return "uv"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # In bundled environments, uv might be bundled as a package
    # or exist in the same directory as the executable.
    return "uv"

def run_uv(args: List[str], capture_output: bool = False) -> subprocess.CompletedProcess:
    uv_exe = get_uv_executable()
    cmd = [uv_exe] + args
    
    # In bundled environments, ensure the correct environment is targeted
    site_packages = get_or_create_site_packages_dir()
    
    try:
        return subprocess.run(cmd, capture_output=capture_output, check=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"uv command failed: {' '.join(cmd)}")
        if e.stderr:
            logger.error(e.stderr)
        raise

def uv_install(packages: List[str], target: Optional[Path] = None):
    if not packages:
        return
    
    args = ["pip", "install"]
    if target:
        args.extend(["--target", str(target)])
    
    args.extend(packages)
    run_uv(args)

def uv_uninstall(packages: List[str], target: Optional[Path] = None):
    if not packages:
        return

    args = ["pip", "uninstall"]
    args.extend(packages)
    run_uv(args)

def uv_purge(unused_packages: List[str], target: Optional[Path] = None):
    if not unused_packages:
        return
    
    logger.info(f"Purging unused packages: {', '.join(unused_packages)}")
    uv_uninstall(unused_packages, target)
