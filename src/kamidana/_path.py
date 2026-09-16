# xxx: hack for template name resolution by relative path from current template.

import os.path
import posixpath
import typing as t
import jinja2
from collections import namedtuple

_Original = namedtuple("_Original", "path, where")


def is_physical_path(name: str) -> bool:
    """a physical file path starts with './', '../' or '/'

    (i.e. any name starting with '.' or '/')
    """
    return name.startswith((".", "/"))


def split_package_spec(name: str) -> t.Tuple[str, str]:
    """split a package template spec into (package, resource path)

    e.g. "mypkg/templates/main.j2" -> ("mypkg", "templates/main.j2")
    """
    package, _, resource = name.partition("/")
    return package, resource


class XTemplatePathNotFound(Exception):
    def __init__(self, msg: str, *, exc: t.Optional[Exception] = None) -> None:
        super().__init__(msg)
        self.exc = exc

    def __str__(self) -> str:
        return str(self.exc)

    @property
    def original_context(self) -> _Original:
        return x_get_original_context(self.args[0])


class _TemplatePath(str):
    original: t.Optional[_Original]


def TemplatePath(
    path: str, *, original: t.Optional[_Original] = None
) -> _TemplatePath:
    p = _TemplatePath(path)
    p.original = original
    return p


def x_get_original_context(path: str) -> _Original:
    return t.cast(
        _Original, getattr(path, "original", None) or _Original(path=path, where=None)
    )


class ResolvingByRelativePathEnvironment(jinja2.Environment):
    # @override
    def join_path(self, path: str, where: str | None = None) -> str:
        if where is None or path.startswith("/"):
            template_path = path
        elif is_physical_path(where):
            template_path = os.path.normpath(
                os.path.join(os.path.abspath(os.path.dirname(where)), path)
            )
        else:
            # where is a package template spec (e.g. "mypkg/templates/main.j2")
            base = posixpath.dirname(where)
            template_path = posixpath.normpath(posixpath.join(base, path))
        return TemplatePath(template_path, original=_Original(path=path, where=where))
