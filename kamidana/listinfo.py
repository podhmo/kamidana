import typing as t
import inspect
import os.path
from collections import defaultdict, OrderedDict
from importlib import import_module
import jinja2.ext
from .compat import importlib_resources

Description = t.NewType("Description", str)


def collect_extensions_info(
    *, _candidates=["jinja2.ext", "kamidana.extensions"]
) -> t.Dict[str, Description]:
    extensions = defaultdict(list)
    for modname in _candidates:
        m = import_module(modname)
        for name, v in m.__dict__.items():
            if not inspect.isclass(v):
                continue
            if not issubclass(v, jinja2.ext.Extension):
                continue
            if v == jinja2.ext.Extension:
                continue
            extensions[v].append(f"{modname}.{name}")

    info = OrderedDict()
    for cls, fullnames in extensions.items():
        fullname = sorted(fullnames, key=lambda x: len(x))[0]
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


def listinfo():
    d = OrderedDict()
    d["extensions"] = collect_extensions_info()
    d["additional_modules"] = collect_additional_modules_info()
    return d
