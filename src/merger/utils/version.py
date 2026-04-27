import importlib.metadata


_VERSION_CACHE = None


def get_version() -> str:
    """
    Retrieve the version of the merger-cli package using importlib.metadata.
    """
    global _VERSION_CACHE
    if _VERSION_CACHE is not None:
        return _VERSION_CACHE

    try:
        _VERSION_CACHE = importlib.metadata.version("merger-cli")
        return _VERSION_CACHE
        
    except importlib.metadata.PackageNotFoundError:
        _VERSION_CACHE = "unknown"
        return _VERSION_CACHE
