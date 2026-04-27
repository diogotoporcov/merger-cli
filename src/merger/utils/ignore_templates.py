from importlib import resources
from typing import List

from ..exceptions import UnknownIgnoreTemplate


def list_ignore_templates() -> List[str]:
    # Use the legacy API for Python 3.8 support
    try:
        # For Python 3.9+
        base = resources.files("merger.resources.ignore_files")
        templates = sorted(
            p.name[:-7].upper()
            for p in base.iterdir()
            if p.is_file() and p.name.endswith(".ignore")
        )
        
    except AttributeError:
        # Fallback for Python 3.8
        files = resources.contents("merger.resources.ignore_files")
        templates = sorted(
            name[:-7].upper()
            for name in files
            if name.endswith(".ignore")
        )

    if "DEFAULT" in templates:
        templates.remove("DEFAULT")
        return ["DEFAULT"] + templates
    return templates


def read_ignore_template(template: str) -> str:
    name = template.lower().strip()
    filename = f"{name}.ignore"

    try:
        # For Python 3.9+
        base = resources.files("merger.resources.ignore_files")
        path = base.joinpath(filename)
        if not path.is_file():
            available = list_ignore_templates()
            raise UnknownIgnoreTemplate(
                f"Unknown ignore template '{template}'. "
                f"Available templates: {', '.join(available)}"
            )
        return path.read_text(encoding="utf-8")
        
    except AttributeError:
        # Fallback for Python 3.8
        try:
            return resources.read_text("merger.resources.ignore_files", filename, encoding="utf-8")
            
        except (FileNotFoundError, ImportError):
            available = list_ignore_templates()
            raise UnknownIgnoreTemplate(
                f"Unknown ignore template '{template}'. "
                f"Available templates: {', '.join(available)}"
            )
