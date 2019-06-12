from kamidana import as_global
from kamidana.compat import importlib_resources


@as_global
def get_grammar():
    return importlib_resources.read_text("lib2to3", "Grammar.txt")
