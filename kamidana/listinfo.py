import inspect
from collections import defaultdict, OrderedDict

import jinja2.ext


def collect_extensions_info():
    extensions = defaultdict(list)
    for name, v in jinja2.ext.__dict__.items():
        if not inspect.isclass(v):
            continue
        if not issubclass(v, jinja2.ext.Extension):
            continue
        if v == jinja2.ext.Extension:
            continue
        extensions[v].append(name)

    info = OrderedDict()
    for cls, names in extensions.items():
        name = sorted(names, key=lambda x: len(x))[0]
        fullname = f"{cls.__module__}.{name}"
        oneline_doc = inspect.getdoc(cls).strip().split("\n", 1)[0]
        info[fullname] = oneline_doc
    return info
