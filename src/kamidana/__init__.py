# -*- coding:utf-8 -*-
from collections import defaultdict

MARKER_TAG = "_kamidana_marker"
IS_GENERATOR_TAG = "_kamidana_is_generator"


def create_marker(name, is_generator=False):
    def decorator(fn):
        if not hasattr(fn, MARKER_TAG):
            setattr(fn, MARKER_TAG, [])
        getattr(fn, MARKER_TAG).append(name)
        setattr(fn, IS_GENERATOR_TAG, is_generator)
        return fn

    return decorator


as_filter = create_marker("filters")
as_global = create_marker("globals")
as_test = create_marker("tests")
as_globals_generator = create_marker("globals", is_generator=True)


def collect_marked_items(module):
    marked = defaultdict(dict)
    for v in module.__dict__.values():
        names = getattr(v, MARKER_TAG, None) or []
        for name in names:
            if name is not None:
                if getattr(v, IS_GENERATOR_TAG, False):
                    marked[name].update(v())
                else:
                    marked[name][v.__name__] = v
    return marked
