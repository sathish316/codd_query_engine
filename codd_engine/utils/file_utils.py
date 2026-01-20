import os


def expand_path(path: str) -> str:
    """Expand environment variables and ~ in path."""
    return os.path.expandvars(os.path.expanduser(path))
