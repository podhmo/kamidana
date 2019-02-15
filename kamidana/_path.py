# xxx: hack for template name resolution by relative path from current template.

import os.path
import jinja2
from collections import namedtuple

_Original = namedtuple("_Original", "path, where")


class XTemplatePathNotFound(Exception):
    def __init__(self, msg, *, exc=None):
        super().__init__(msg)
        self.exc = exc

    def __str__(self):
        return str(self.exc)

    @property
    def original_context(self):
        return x_get_original_context(self.args[0])


class _TemplatePath(str):
    pass


def TemplatePath(path, *, original=None):
    path = _TemplatePath(path)
    path.original = original
    return path


def x_get_original_context(path):
    return getattr(path, "original", None) or _Original(path=path, where=None)


class ResolvingByRelativePathEnvironment(jinja2.Environment):
    # @override
    def join_path(self, path: str, where: str = None) -> str:
        if where is None:
            template_path = path
        else:
            template_path = os.path.normpath(
                os.path.join(os.path.abspath(os.path.dirname(where)), path)
            )
        return TemplatePath(template_path, original=_Original(path=path, where=where))
