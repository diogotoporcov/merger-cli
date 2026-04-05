import importlib.metadata
from typing import List

from ..logging import logger


def check_and_warn_dependencies(requirements: List[str], plugin_name: str) -> None:
    """Checks if dependencies are installed and warns the user if they are missing."""
    try:
        from packaging.requirements import Requirement
    except ImportError:
        logger.debug(f"Could not verify dependencies for {plugin_name}: 'packaging' is not installed.")
        return

    missing = []
    for req_str in requirements:
        try:
            req = Requirement(req_str)
            installed_version = importlib.metadata.version(req.name)
            if not req.specifier.contains(installed_version, prereleases=True):
                missing.append(req_str)

        except importlib.metadata.PackageNotFoundError:
            missing.append(req_str)

        except Exception as e:
            logger.warning(f"Could not verify dependency '{req_str}': {e}")

    if missing:
        logger.warning(
            f"The following dependencies for {plugin_name} are missing or unsatisfied: "
            f"{', '.join(missing)}"
        )
        logger.warning("Please install them manually using: pip install " + " ".join(missing))
