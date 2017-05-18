import sys
from dictknife import deepmerge
from dictknife import loading
from dictknife.langhelpers import reify
from magicalimport import import_module
from . import collect_marked_items
from .interfaces import ITemplateLoader


class TemplateLoader(ITemplateLoader):
    def __init__(self, data_path_list, additional_path, format=None):
        self.data_path_list = data_path_list
        self.additional_path = additional_path
        self.format = format

    def load(self, filename):
        with open(filename) as rf:
            return rf.read()

    @reify
    def data(self):
        data = deepmerge(*[loading.loadfile(d) for d in self.data_path_list], override=True)
        if self.format is not None:
            data = deepmerge(data, loading.load(sys.stdin, format=self.format), override=True)
        return data

    @reify
    def additionals(self):
        if self.additional_path is None:
            return {}
        m = import_module(self.additional_path)
        return collect_marked_items(m)
