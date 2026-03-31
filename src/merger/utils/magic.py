import platform
import shutil

import magic


def get_libmagic_install_help() -> str:
    """
    Returns platform-specific instructions to install libmagic.
    """
    system = platform.system()
    if system == "Windows":
        return "Install 'python-magic-bin' via pip: 'pip install python-magic-bin'"

    elif system == "Darwin":
        return "Install 'libmagic' via Homebrew: 'brew install libmagic'"

    elif system == "Linux":
        if shutil.which("apt-get"):
            return "Install 'libmagic' via apt: 'sudo apt-get install libmagic1'"

        elif shutil.which("dnf"):
            return "Install 'libmagic' via dnf: 'sudo dnf install file-libs'"

        elif shutil.which("pacman"):
            return "Install 'libmagic' via pacman: 'sudo pacman -S file'"

        return "Install 'libmagic' using your package manager."

    return "Install the 'libmagic' library on your system."

def check_libmagic_availability() -> None:
    """
    Checks if libmagic is available. If not, raises a RuntimeError with installation instructions.
    """
    try:
        magic.from_buffer(b"", mime=True)

    except Exception as e:
        # Check if it's a libmagic related error
        error_msg = str(e).lower()
        libmagic_indicators = ["libmagic", "not found", "failed to find", "import"]
        
        if any(indicator in error_msg for indicator in libmagic_indicators) or isinstance(e, (ImportError, OSError)):
            raise RuntimeError(
                f"libmagic is required but not found or failed to load: {e}\n"
                f"{get_libmagic_install_help()}"
            ) from e
        
        # If it's a real magic error, report it
        raise RuntimeError(f"Error while identifying file type with libmagic: {e}") from e
