"""
accessing environemt variable, via env()
"""
import os
from kamidana import as_filter, as_global


@as_filter
@as_global
def env(envname, *, default=""):
    return os.environ.get(envname, default)
