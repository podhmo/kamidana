import sys
import logging
from dictknife import deepmerge
from dictknife import loading
from dictknife.langhelpers import reify
from magicalimport import import_module
from . import collect_marked_items
from .interfaces import ITemplateLoader
from ._path import XTemplatePathNotFound

logger = logging.getLogger(__name__)


class TemplateLoader(ITemplateLoader):
    def __init__(self, data_path_list, additional_path_list, extensions, format=None):
        self.data_path_list = data_path_list
        self.additional_path_list = additional_path_list
        self.extensions = extensions
        self.format = format
        self._cache = {}

    def load(self, filename):
        data = self._cache.get(filename)
        if data is not None:
            return data

        try:
            with open(filename) as rf:
                logger.debug("load: %s", filename)
                data = self._cache[filename] = rf.read()
            return data
        except FileNotFoundError as e:
            raise XTemplatePathNotFound(filename, exc=e) from None

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
                m = import_module(path)
            except ImportError:
                m = import_module("kamidana.additionals.{}".format(path))
            d = deepmerge(d, collect_marked_items(m))
        return d
