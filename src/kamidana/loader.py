from __future__ import annotations

import sys
import os.path
import linecache
import logging
import importlib.resources
from functools import cached_property
from dictknife.deepmerge import deepmerge
from dictknife import loading
from typing import TYPE_CHECKING
import typing as t
from ._import import import_module
from . import collect_marked_items
from .interfaces import ITemplateLoader
from ._path import (
    XTemplatePathNotFound,
    is_physical_path,
    split_package_spec,
)

if TYPE_CHECKING:
    import importlib.abc

logger = logging.getLogger(__name__)

# a data source is a plain file path, or a (kind, value) tuple produced by the
# CLI: ("file", path) for -d/--data and ("json", parsed-object) for --data-json.
DataSource = t.Union[str, t.Tuple[str, t.Any]]


class TemplateLoader(ITemplateLoader):
    def __init__(
        self,
        data_path_list: t.List[DataSource],
        additional_path_list: t.List[str],
        extensions: t.List[str],
        format: t.Optional[str] = None,
    ) -> None:
        self.data_path_list = data_path_list
        self.additional_path_list = additional_path_list
        self.extensions = extensions
        self.format = format

    def load(
        self, filename: str
    ) -> t.Tuple[str, str, t.Optional[t.Callable[[], bool]]]:
        # -> source, path, unmodified_fn
        if is_physical_path(filename):
            return self._load_from_file(filename)
        return self._load_from_package(filename)

    def _load_from_file(
        self, filename: str
    ) -> t.Tuple[str, str, t.Optional[t.Callable[[], bool]]]:
        try:
            with open(filename) as rf:
                logger.debug("load: %s", filename)
                return rf.read(), filename, None
        except FileNotFoundError as e:
            exc = FileNotFoundError("{}. ({})".format(e, _SPEC_NOTE))
            raise XTemplatePathNotFound(filename, exc=exc).with_traceback(e.__traceback__)

    def _load_from_package(
        self, filename: str
    ) -> t.Tuple[str, str, t.Optional[t.Callable[[], bool]]]:
        package, resource = split_package_spec(filename)
        if not package or not resource:
            raise XTemplatePathNotFound(filename, exc=_missing_spec_exc(filename))
        try:
            anchor = importlib.resources.files(package)
        except (ImportError, TypeError, AttributeError) as e:
            exc = _package_not_found_exc(package, filename, e)
            raise XTemplatePathNotFound(filename, exc=exc).with_traceback(e.__traceback__)

        target = anchor
        for part in resource.split("/"):
            target = target.joinpath(part)
        try:
            source = target.read_text(encoding="utf-8")
        except (FileNotFoundError, IsADirectoryError, NotADirectoryError) as e:
            exc = _resource_not_found_exc(package, resource, anchor)
            raise XTemplatePathNotFound(filename, exc=exc).with_traceback(e.__traceback__)

        logger.debug("load: %s (package=%s)", filename, package)
        # make the source visible to linecache, for gentle error reporting
        lines = source.splitlines(True)
        linecache.cache[filename] = (len(source), None, lines, filename)
        return source, filename, None

    @cached_property
    def data(self) -> t.Dict[str, t.Any]:
        ds: t.List[t.Dict[str, t.Any]] = []
        for source in self.data_path_list:
            if isinstance(source, str):
                ds.append(loading.loadfile(source))
            elif source[0] == "json":
                ds.append(source[1])
            else:
                ds.append(loading.loadfile(source[1]))
        data: t.Dict[str, t.Any] = deepmerge(*ds, override=True)
        if self.format is not None:
            data = deepmerge(
                data, loading.load(sys.stdin, format=self.format), override=True
            )
        return data

    @cached_property
    def additionals(self) -> t.Dict[str, t.Dict[str, t.Any]]:
        d: t.Dict[str, t.Dict[str, t.Any]] = {}
        for path in self.additional_path_list:
            try:
                m = import_module(path, cwd=True)
            except ImportError as e:
                # when the file exists, the error came from inside the
                # module -- surface it instead of masking it behind the
                # builtin-module fallback.
                if path.endswith(".py") and os.path.exists(path):
                    raise
                module_name = path[:-3] if path.endswith(".py") else path
                fallback = "kamidana.additionals.{}".format(module_name)
                try:
                    m = import_module(fallback, cwd=True)
                except ImportError:
                    raise ImportError(
                        "module not found: {} (also tried {})".format(path, fallback)
                    ) from e
            d = deepmerge(d, collect_marked_items(m))
        return d


_SPEC_NOTE = (
    "a template name is a file if it starts with './', '../' or '/';"
    " otherwise it is a template in a python package ('<package>/<path>')"
)


def _missing_spec_exc(filename: str) -> FileNotFoundError:
    if os.path.exists(filename):
        msg = (
            '"{0}" exists in the current directory, but "{0}" is interpreted'
            " as a template in a python package. to load the file, pass"
            ' "./{0}". ({1})'.format(filename, _SPEC_NOTE)
        )
    else:
        msg = (
            '"{0}" is interpreted as a template in a python package, but it'
            " is not in '<package>/<path>' form. ({1})".format(
                filename, _SPEC_NOTE
            )
        )
    return FileNotFoundError(msg)


def _package_not_found_exc(
    package: str, filename: str, e: Exception
) -> FileNotFoundError:
    if os.path.exists(filename):
        hint = ' the file exists; to load it, pass "./{}".'.format(filename)
    else:
        hint = ""
    msg = (
        'python package "{}" is not found, while loading template "{}"'
        " ({}).{} ({})".format(package, filename, e, hint, _SPEC_NOTE)
    )
    return FileNotFoundError(msg)


def _resource_not_found_exc(
    package: str, resource: str, anchor: importlib.abc.Traversable
) -> FileNotFoundError:
    msg = (
        'template "{}" is not found in package "{}" (at {}). ({})'.format(
            resource, package, anchor, _SPEC_NOTE
        )
    )
    return FileNotFoundError(msg)
