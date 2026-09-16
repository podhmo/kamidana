import importlib
import os.path
import sys
import typing as t
from types import ModuleType


def _module_id(path: str) -> str:
    dirname = os.path.dirname(path)
    basename = os.path.basename(path)
    return "{}.{}".format(dirname.replace("/", "_"), basename.rsplit(".py", 1)[0])


def import_module(
    module_path: str, *, here: str | None = None, cwd: bool = True
) -> ModuleType:
    """import a module by dotted name (e.g. "foo.bar") or file path (e.g. "foo/bar.py")

    - ``here``: base directory used to resolve a relative file path.
    - ``cwd``: resolve a relative file path against the current directory.
    """
    _, ext = os.path.splitext(module_path)
    if ext == ".py":
        return _import_from_path(module_path, here=here, cwd=cwd)
    return importlib.import_module(module_path)


def _import_from_path(
    path: str, *, here: str | None = None, cwd: bool = True
) -> ModuleType:
    if here is None:
        if not cwd:
            raise ValueError("one of here= or cwd=True is required")
    else:
        path = os.path.join(here, path)

    # keep the path relative (when possible) so that it appears as a
    # relative path in tracebacks. (spec_from_file_location() would
    # normalize __file__ to an absolute path, so the module is created
    # and exec'ed by hand.)
    lookup_path = os.path.normpath(os.path.abspath(path))
    if not os.path.exists(lookup_path):
        raise ModuleNotFoundError("module file is not found: {}".format(path))

    module_id = _module_id(path.replace(os.sep, "/"))
    if module_id in sys.modules:
        return sys.modules[module_id]

    module = ModuleType(module_id)
    module.__file__ = path
    sys.modules[module_id] = module
    with open(lookup_path) as rf:
        code = compile(rf.read(), path, "exec")
    exec(code, module.__dict__)
    return module


def import_symbol(
    sym: str, *, ns: str | None = None, sep: str = ":", cwd: bool = True
) -> t.Any:
    """import a symbol, e.g. "pkg.mod:attr" or "attr" resolved inside ``ns``."""
    if ns is not None and sep not in sym:
        sym = "{}{}{}".format(ns, sep, sym)
    module_path, _, name = sym.rpartition(sep)
    module = import_module(module_path, cwd=cwd)
    try:
        return getattr(module, name)
    except AttributeError as e:
        raise ImportError(e)
