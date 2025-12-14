import hashlib
from pathlib import Path


def hash_from_file(path: Path, length: int = 12) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()[:length]
