from kamidana import as_global
from importlib import resources


@as_global
def get_grammar():
    return resources.read_text("lib2to3", "Grammar.txt")
