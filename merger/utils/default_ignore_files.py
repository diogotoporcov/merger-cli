from importlib import resources
from typing import List

from ..exceptions.exceptions import UnknownIgnoreTemplate


def list_ignore_templates() -> List[str]:
    base = resources.files("merger.resources.ignore_files")

    return sorted(
        p.name.removesuffix(".ignore")
        for p in base.iterdir()
        if p.is_file() and p.name.endswith(".ignore")
    )


def read_ignore_template(template: str) -> str:
    name = template.lower().strip()
    filename = f"{name}.ignore"

    base = resources.files("merger.resources.ignore_files")
    path = base.joinpath(filename)

    if not path.is_file():
        available = list_ignore_templates()
        raise UnknownIgnoreTemplate(
            f"Unknown ignore template '{template}'. "
            f"Available templates: {', '.join(available)}"
        )

    return path.read_text(encoding="utf-8")
