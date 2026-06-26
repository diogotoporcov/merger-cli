from pathlib import Path
from typing import Set


def read_merger_ignore_file(filepath: Path) -> Set[str]:
    patterns: Set[str] = set()

    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.add(line)

    return patterns
