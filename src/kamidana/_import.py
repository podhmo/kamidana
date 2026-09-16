from __future__ import annotations

import hashlib
import importlib
import os.path
import sys
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typing as t

# standalone files (not inside a package) are exec'ed into detached
# ModuleType objects; the authoritative cache is keyed on real path so
# that two spellings of one file ("x.py" vs "./x.py") share the module.
_standalone_modules: dict[str, ModuleType] = {}


def _module_id(path: str) -> str:
    dirname = os.path.dirname(path)
    basename = os.path.splitext(os.path.basename(path))[0]
    return "{}.{}".format(dirname.replace("/", "_"), basename)


def import_module(
    module_path: str, *, here: str | None = None, cwd: bool = True
) -> ModuleType:
    """import a module by dotted name (e.g. "foo.bar") or file path (e.g. "foo/bar.py")

    - ``here``: base directory used to resolve a relative file path.
    - ``cwd``: resolve a relative file path against the current directory.

    A file living inside a package (a directory containing ``__init__.py``)
    is imported as a member of that package, so ``from . import x`` works
    inside it.  A standalone file is exec'ed as a detached module, where
    relative imports are not available.
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

    lookup_path = os.path.normpath(os.path.abspath(path))
    if not os.path.exists(lookup_path):
        raise ModuleNotFoundError("module file is not found: {}".format(path))

    pkg = _package_context(lookup_path)
    if pkg is not None:
        return _import_as_package_member(pkg, lookup_path=lookup_path)
    return _import_as_standalone(path, lookup_path)


def _package_context(lookup_path: str) -> t.Tuple[int, t.List[str]] | None:
    """(depth, dotted name parts) when the file lives inside a package.

    Walks up the chain of directories containing ``__init__.py``, starting
    at the file's own directory.  ``depth`` is the number of package
    directories found; the directory above them is the import root.
    """
    if os.path.basename(lookup_path) == "__init__.py":
        parts: t.List[str] = []
    else:
        parts = [os.path.splitext(os.path.basename(lookup_path))[0]]
    depth = 0
    dirname = os.path.dirname(lookup_path)
    while os.path.isfile(os.path.join(dirname, "__init__.py")):
        parts.insert(0, os.path.basename(dirname))
        dirname = os.path.dirname(dirname)
        depth += 1
    if depth == 0:
        return None
    return depth, parts


def _import_as_package_member(
    pkg: t.Tuple[int, t.List[str]], *, lookup_path: str
) -> ModuleType:
    depth, parts = pkg

    # mount the directory owning the top-level package on sys.path and
    # go through the normal import machinery so relative imports work.
    # (the resulting __file__ is always absolute -- FileFinder
    # normalizes -- and error reporting relativizes it for display.)
    root = os.path.dirname(lookup_path)
    for _ in range(depth):
        root = os.path.dirname(root)

    root_realpath = os.path.realpath(root)
    # the requested file must win over same-named packages sitting
    # earlier on sys.path (e.g. a stale PYTHONPATH entry): root goes
    # first, any earlier spelling of it is dropped.
    indices = [
        i
        for i, p in enumerate(sys.path)
        if isinstance(p, str) and os.path.realpath(p) == root_realpath
    ]
    if indices != [0]:
        for i in reversed(indices):
            del sys.path[i]
        sys.path.insert(0, root)
    # a same-named package already imported from somewhere else shadows
    # the requested file in sys.modules; evict it so the real one loads.
    top = parts[0]
    pkg_dir = os.path.join(root_realpath, top)
    cached = sys.modules.get(top)
    if cached is not None and not _owns_dir(cached, pkg_dir):
        for name in [n for n in sys.modules if n == top or n.startswith(top + ".")]:
            del sys.modules[name]
    # finder caches are keyed by the sys.path spelling: a leftover
    # FileFinder for "." / "./mypkg" keeps a directory listing (and a
    # path) from an older cwd.  drop every cached finder under this
    # root -- importlib.invalidate_caches() does not evict them.
    for key in [k for k in sys.path_importer_cache if isinstance(k, str)]:
        realpath = os.path.realpath(key)
        if realpath == root_realpath or realpath.startswith(root_realpath + os.sep):
            del sys.path_importer_cache[key]

    dotted_name = ".".join(parts)
    module = importlib.import_module(dotted_name)
    module_file = getattr(module, "__file__", None)
    if module_file is None or os.path.realpath(module_file) != os.path.realpath(
        lookup_path
    ):
        raise ImportError(
            "{!r} resolved to a different file: {} (expected: {})".format(
                dotted_name, module_file, lookup_path
            )
        )
    return module


def _owns_dir(module: ModuleType, pkg_dir_realpath: str) -> bool:
    paths = getattr(module, "__path__", None)
    if paths is None:
        return False
    return any(os.path.realpath(p) == pkg_dir_realpath for p in paths)


def _import_as_standalone(path: str, lookup_path: str) -> ModuleType:
    cache_key = os.path.realpath(lookup_path)
    module = _standalone_modules.get(cache_key)
    if module is not None:
        return module

    # sys.modules is only populated for introspection (cls.__module__
    # lookups by dataclasses, pydantic, pickle, ...).  when the readable
    # name is already taken -- "a/b.py" collides with the package "a.b",
    # or with "x_a/b.py" -- disambiguate deterministically.
    module_id = _module_id(path.replace(os.sep, "/"))
    if module_id in sys.modules:
        suffix = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:8]
        module_id = "{}_{}".format(module_id, suffix)

    # keep the path relative (when possible) so that it appears as a
    # relative path in tracebacks. (spec_from_file_location() would
    # normalize __file__ to an absolute path, so the module is created
    # and exec'ed by hand.)
    module = ModuleType(module_id)
    module.__file__ = path
    module.__package__ = ""
    _standalone_modules[cache_key] = module
    sys.modules[module_id] = module
    try:
        # bytes so that compile() honors a PEP 263 coding declaration
        with open(lookup_path, "rb") as rf:
            code = compile(rf.read(), path, "exec")
        exec(code, module.__dict__)
    except Exception:
        # match normal import semantics: no half-initialized module
        _standalone_modules.pop(cache_key, None)
        sys.modules.pop(module_id, None)
        raise
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
