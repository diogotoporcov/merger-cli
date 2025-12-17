from importlib import resources


def read_default_ignore() -> str:
    with (
        resources.files("merger.resources.ignore_files")
        .joinpath("default.ignore")
        .open("r", encoding="utf-8")
    ) as file:
        return file.read()
