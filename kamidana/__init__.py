# -*- coding:utf-8 -*-
from collections import defaultdict
TAG = "_kamidana_marker"


def create_marker(name):
    def decorator(fn):
        setattr(fn, TAG, name)
        return fn

    return decorator


as_filter = create_marker("filters")
as_global = create_marker("globals")
as_test = create_marker("tests")


def collect_marked_items(module):
    marked = defaultdict(dict)
    for v in module.__dict__.values():
        name = getattr(v, TAG, None)
        if name is not None:
            marked[name][v.__name__] = v
    return marked
