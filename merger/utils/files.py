from pathlib import Path
from typing import Optional, Set


def read_file_bytes(filepath: Path, chunk_size: Optional[int] = None) -> bytes:
    with open(filepath, "rb") as f:
        if chunk_size is not None:
            return f.read(chunk_size)

        return f.read()


def read_merger_ignore_file(filepath: Path) -> Set[str]:
    patterns: Set[str] = set()

    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                patterns.add(line)

    return patterns
