from functools import lru_cache
from pathlib import Path
from typing import Iterable


def matches_pattern(path: Path, root: Path, pattern: str) -> bool:
    """
    Determine whether a filesystem path matches a single custom glob-like pattern,
    evaluated relative to a given root directory.

    The pattern syntax supports:
    - Literal path segments (e.g. "src", "README.md")
    - "*" to match exactly one path segment
    - "**" to match zero or more path segments
    - Embedded "*" within a segment for prefix/suffix matching (e.g. "foo*.py")
    - Leading "/" to anchor the match at the root
    - Leading "./" to anchor the match at the relative path start
    - Trailing "/" to require the matched path to be a directory
    - Trailing ":" to require the matched path to be a file
    - Trailing "!" to disable type qualification and treat any trailing "/"
      or ":" as literal characters in the final path segment

    Matching is performed against the path relative to `root`. If `path` is not
    located under `root`, the function returns False.

    Parameters:
        path: The filesystem path to test.
        root: The root directory used to compute the relative path.
        pattern: The glob-like pattern to match against.

    Returns:
        bool: True if the path matches the pattern; False otherwise.
    """

    try:
        relative_path = path.relative_to(root)

    except ValueError:
        return False

    path_segments = relative_path.parts
    path_len = len(path_segments)
    is_path_dir = path.is_dir()

    has_ignore_type_suffix = pattern.endswith("!")
    if has_ignore_type_suffix:
        pattern = pattern[:-1]

    is_anchored_root = pattern.startswith("/")
    is_anchored_here = pattern.startswith("./")

    is_dir_only = False
    is_file_only = False

    if not has_ignore_type_suffix:
        is_dir_only = pattern.endswith("/")
        is_file_only = pattern.endswith(":")

    if is_anchored_root:
        pattern = pattern[1:]

    if is_anchored_here:
        pattern = pattern[2:]

    if is_dir_only or is_file_only:
        pattern = pattern[:-1]

    pattern_segments = () if pattern == "" else tuple(pattern.split("/"))

    if is_anchored_root or is_anchored_here:
        start_positions = (0,)

    else:
        start_positions = range(path_len + 1)

    @lru_cache(maxsize=None)
    def match_at(pattern_idx: int, segment_idx: int) -> bool:
        while True:
            if pattern_idx == len(pattern_segments):
                if is_dir_only:
                    return segment_idx <= path_len and is_path_dir

                if is_file_only:
                    return segment_idx == path_len and not is_path_dir

                return segment_idx == path_len

            if segment_idx > path_len:
                return False

            pattern_segment = pattern_segments[pattern_idx]

            if pattern_segment == "**":
                if pattern_idx + 1 == len(pattern_segments):
                    return True

                for k in range(segment_idx, path_len + 1):
                    if match_at(pattern_idx + 1, k):
                        return True

                return False

            if segment_idx == path_len:
                return False

            path_segment = path_segments[segment_idx]

            if pattern_segment == "*":
                pattern_idx += 1
                segment_idx += 1
                continue

            if "*" in pattern_segment:
                prefix, _, suffix = pattern_segment.partition("*")
                if not path_segment.startswith(prefix) or not path_segment.endswith(suffix):
                    return False

                pattern_idx += 1
                segment_idx += 1
                continue

            if pattern_segment != path_segment:
                return False

            pattern_idx += 1
            segment_idx += 1

        return False

    for start in start_positions:
        if match_at(0, start):
            return True

    return False


def matches_any_pattern(
    path: Path,
    root: Path,
    patterns: Iterable[str],
) -> bool:
    """
    Determine whether a filesystem path matches at least one custom glob-like
    pattern from a collection of patterns, evaluated relative to a given root
    directory.

    Each pattern is interpreted using the same matching rules as `matches_pattern`,
    including support for:
    - Literal path segments
    - "*" to match exactly one path segment
    - "**" to match zero or more path segments
    - Embedded "*" within a segment for prefix/suffix matching
    - Leading "/" or "./" for anchoring
    - Trailing "/" to require directories
    - Trailing ":" to require files
    - Trailing "!" to disable type qualification and treat any trailing "/"
      or ":" as literal characters in the final path segment

    Matching is performed against the path relative to `root`. If `path` is not
    located under `root`, the function returns False.

    Parameters:
        path: The filesystem path to test.
        root: The root directory used to compute the relative path.
        patterns: An iterable of glob-like patterns to match against.

    Returns:
        bool: True if the path matches at least one pattern; False otherwise.
    """

    return any(
        matches_pattern(path, root, pattern)
        for pattern in patterns
    )
