"""
accessing environemt variable, via env()
"""
import os
from kamidana import as_filter, as_global


@as_filter
@as_global
def env(envname: str, *, default: str = "") -> str:
    return os.environ.get(envname, default)
