from kamidana import as_filter
from . import nonexistent_module


@as_filter
def shout(text):
    return text.upper()
