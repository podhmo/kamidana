import typing as t
import inspect
import os.path
from collections import defaultdict
from importlib import import_module
from importlib import resources
import jinja2.ext

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

    info = {}
    for cls, fullnames in extensions.items():
        fullname = sorted(fullnames, key=lambda x: len(x))[0]
        doc = inspect.getdoc(cls) or ""
        info[fullname] = Description(doc.strip().split("\n", 1)[0])
    return info


def collect_additional_modules_info() -> t.Dict[str, Description]:
    info = {}
    contents = resources.files("kamidana.additionals")
    for resource in contents.iterdir():
        filename = resource.name
        if not filename.endswith(".py"):
            continue
        if filename == "__init__.py":
            continue
        modulename = f"kamidana.additionals.{os.path.splitext(filename)[0]}"
        doc = inspect.getdoc(import_module(modulename)) or ""
        info[modulename] = Description(doc)
    return info


def listinfo():
    d = {}
    d["extensions"] = collect_extensions_info()
    d["additional_modules"] = collect_additional_modules_info()
    return d
