import sys
import os.path
import linecache
import logging
import importlib.resources
from dictknife import deepmerge
from dictknife import loading
from dictknife.langhelpers import reify
from ._import import import_module
from . import collect_marked_items
from .interfaces import ITemplateLoader
from ._path import (
    XTemplatePathNotFound,
    is_physical_path,
    split_package_spec,
)

logger = logging.getLogger(__name__)


class TemplateLoader(ITemplateLoader):
    def __init__(self, data_path_list, additional_path_list, extensions, format=None):
        self.data_path_list = data_path_list
        self.additional_path_list = additional_path_list
        self.extensions = extensions
        self.format = format

    def load(self, filename):  # -> source, path, unmodified_fn
        if is_physical_path(filename):
            return self._load_from_file(filename)
        return self._load_from_package(filename)

    def _load_from_file(self, filename):
        try:
            with open(filename) as rf:
                logger.debug("load: %s", filename)
                return rf.read(), filename, None
        except FileNotFoundError as e:
            raise XTemplatePathNotFound(filename, exc=e).with_traceback(e.__traceback__)

    def _load_from_package(self, filename):
        package, resource = split_package_spec(filename)
        if not package or not resource:
            raise XTemplatePathNotFound(filename, exc=_missing_spec_exc(filename))
        try:
            anchor = importlib.resources.files(package)
        except (ImportError, TypeError, AttributeError) as e:
            raise XTemplatePathNotFound(
                filename, exc=_package_not_found_exc(package, filename, e)
            ).with_traceback(e.__traceback__)

        target = anchor
        for part in resource.split("/"):
            target = target.joinpath(part)
        try:
            source = target.read_text(encoding="utf-8")
        except (FileNotFoundError, IsADirectoryError, NotADirectoryError) as e:
            raise XTemplatePathNotFound(
                filename,
                exc=FileNotFoundError(
                    'template "{}" is not found in package "{}"'.format(
                        resource, package
                    )
                ),
            ).with_traceback(e.__traceback__)

        logger.debug("load: %s (package=%s)", filename, package)
        # make the source visible to linecache, for gentle error reporting
        lines = source.splitlines(True)
        linecache.cache[filename] = (len(source), None, lines, filename)
        return source, filename, None

    @reify
    def data(self):
        data = deepmerge(
            *[loading.loadfile(d) for d in self.data_path_list], override=True
        )
        if self.format is not None:
            data = deepmerge(
                data, loading.load(sys.stdin, format=self.format), override=True
            )
        return data

    @reify
    def additionals(self):
        d = {}
        for path in self.additional_path_list:
            try:
                m = import_module(path, cwd=True)
            except ImportError:
                m = import_module("kamidana.additionals.{}".format(path), cwd=True)
            d = deepmerge(d, collect_marked_items(m))
        return d


def _missing_spec_exc(filename):
    if os.path.exists(filename):
        msg = (
            '"{0}" exists in the current directory, but "{0}" is interpreted'
            " as a template in a python package. to load the file, pass"
            ' "./{0}"'.format(filename)
        )
    else:
        msg = (
            '"{0}" is interpreted as a template in a python package, but it'
            " is not in '<package>/<path>' form. a physical path must start"
            " with './' or '/' (e.g. './{0}'); a package template looks like"
            " '<package>/<path>'".format(filename)
        )
    return FileNotFoundError(msg)


def _package_not_found_exc(package, filename, e):
    if os.path.exists(filename):
        hint = ' the file exists; pass "./{}" to load it.'.format(filename)
    else:
        hint = (
            " if it is a file, a physical path must start with './' or '/'."
        )
    msg = 'python package "{}" is not found, while loading template "{}" ({}).{}'.format(
        package, filename, e, hint
    )
    return FileNotFoundError(msg)
