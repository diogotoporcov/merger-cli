from importlib.metadata import version, PackageNotFoundError
import tomllib
from pathlib import Path


def get_version() -> str:
    try:
        return version("merger-cli")

    except PackageNotFoundError:
        pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
        try:
            with pyproject_path.open("rb") as file:
                data = tomllib.load(file)
            return data["project"]["version"]

        except Exception:
            return "unknown"
