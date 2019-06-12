from kamidana import as_global
from kamidana.compat import importlib_resources


@as_global
def about_kamidana():
    return importlib_resources.read_text("kamidana", "data.txt")
