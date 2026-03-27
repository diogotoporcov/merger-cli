import pathspec
from pathlib import Path
from typing import Iterable


class PatternSpec:
    """
    A container for compiled path patterns with support for type-based filtering.
    """
    def __init__(self, spec_either: pathspec.PathSpec, spec_file_only: pathspec.PathSpec, has_empty_pattern: bool = False):
        self.spec_either = spec_either
        self.spec_file_only = spec_file_only
        self.has_empty_pattern = has_empty_pattern


def compile_patterns(patterns: Iterable[str]) -> PatternSpec:
    """
    Compile an iterable of glob-like patterns into a PatternSpec object.
    Normalized to handle common non-standard prefixes like './' and 
    type qualifiers like ':' for files and '!' for literal escaping.
    """
    either_patterns = []
    file_only_patterns = []
    has_empty_pattern = False

    for p in patterns:
        if not p:
            has_empty_pattern = True
            continue

        # Normalize ./ to / for anchoring
        if p.startswith("./"):
            p = "/" + p[2:]

        # Suffix handling
        is_literal = False
        is_file_only = False
        if p.endswith('!'):
            is_literal = True
            p = p[:-1]

        elif p.endswith(':'):
            is_file_only = True
            p = p[:-1]

        if not is_literal:
            is_anchored = p.startswith("/")
            is_dir_only = p.endswith("/")
            segments = [s for s in p.split('/') if s and s != '.']
            p = "/".join(segments)
            if is_anchored:
                p = "/" + p

            if is_dir_only and not p.endswith("/"):
                p = p + "/"

        if p == "/" or not p:
            has_empty_pattern = True
            continue

        if is_file_only:
            file_only_patterns.append(p)

        else:
            either_patterns.append(p)

    return PatternSpec(
        spec_either=pathspec.PathSpec.from_lines('gitwildmatch', either_patterns),
        spec_file_only=pathspec.PathSpec.from_lines('gitwildmatch', file_only_patterns),
        has_empty_pattern=has_empty_pattern
    )


def matches_any_pattern(
    path: Path,
    root: Path,
    spec: PatternSpec,
) -> bool:
    """
    Determine whether a filesystem path matches at least one pattern from
    the given PatternSpec, evaluated relative to a given root directory.
    """
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        return False

    path_str = relative_path.as_posix()
    is_dir = path.is_dir()

    # Empty pattern matches only the root
    if spec.has_empty_pattern and path_str == ".":
        return True

    # pathspec matches against strings. 
    # For directories, pathspec expects a trailing slash to match directory-only patterns.
    if is_dir and not path_str.endswith('/'):
        path_str += '/'

    # Check for patterns that match either file or directory (including standard patterns and / suffixes)
    if spec.spec_either.match_file(path_str):
        return True

    # Check for file-only patterns (:)
    if not is_dir and spec.spec_file_only.match_file(path_str):
        return True

    return False


def matches_pattern(path: Path, root: Path, pattern: str) -> bool:
    """
    Determine whether a filesystem path matches a single pattern,
    evaluated relative to a given root directory.
    """
    spec = compile_patterns([pattern])
    return matches_any_pattern(path, root, spec)
