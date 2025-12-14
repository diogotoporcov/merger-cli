import fnmatch
from typing import Iterable


def matches_pattern(path: str, glob_pattern: str) -> bool:
    return (
            fnmatch.fnmatch(path, glob_pattern)
            or fnmatch.fnmatch(path.rsplit("/", 1)[1], glob_pattern)
    )


def matches_any_pattern(path: str, glob_patterns: Iterable[str]) -> bool:
    return any(
        matches_pattern(path, pattern)
        for pattern in glob_patterns
    )
