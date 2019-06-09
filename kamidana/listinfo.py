import typing as t
import inspect
import os.path
from collections import defaultdict, OrderedDict
from importlib import import_module
import jinja2.ext
from .compat import importlib_resources

Description = t.NewType(str)


def collect_extensions_info() -> t.Dict[str, Description]:
    extensions = defaultdict(list)
    for name, v in jinja2.ext.__dict__.items():
        if not inspect.isclass(v):
            continue
        if not issubclass(v, jinja2.ext.Extension):
            continue
        if v == jinja2.ext.Extension:
            continue
        extensions[v].append(name)

    info = OrderedDict()
    for cls, names in extensions.items():
        name = sorted(names, key=lambda x: len(x))[0]
        fullname = f"{cls.__module__}.{name}"
        oneline_doc = inspect.getdoc(cls).strip().split("\n", 1)[0]
        info[fullname] = oneline_doc
    return info


def collect_additional_modules_info() -> t.Dict[str, Description]:
    info = OrderedDict()
    contents = importlib_resources.contents("kamidana.additionals")
    for filename in contents:
        if not filename.endswith(".py"):
            continue
        if filename == "__init__.py":
            continue
        modulename = f"kamidana.additionals.{os.path.splitext(filename)[0]}"
        info[modulename] = inspect.getdoc(import_module(modulename))
    return info
