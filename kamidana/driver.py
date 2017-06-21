import jinja2
import jinja2.ext as ext
from dictknife import loading
from dictknife.langhelpers import reify
from .interfaces import IDriver


def _make_environment(load, additionals, extensions):
    extensions.append(ext.with_)
    env = jinja2.Environment(
        loader=jinja2.FunctionLoader(load),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=extensions,
    )
    for name, defs in additionals.items():
        getattr(env, name).update(defs)
    return env


class Driver(IDriver):
    def __init__(self, loader, format):
        self.loader = loader
        self.format = format

    @reify
    def environment(self):
        return _make_environment(self.loader.load, self.loader.additionals, self.loader.extensions)

    def transform(self, t):
        return t.render(**self.loader.data)

    def load(self, template_file):
        return self.environment.get_or_select_template(template_file)

    def dump(self, d, dst):
        fmt = self.format
        if fmt != "raw":
            d = loading.loads(d, format=fmt)
        return loading.dumpfile(d, format=fmt)

    def run(self, src, dst):
        data = self.load(src)
        result = self.transform(data)
        return self.dump(result, dst)


class ContextDumpDriver(IDriver):
    def __init__(self, loader, format):
        self.loader = loader
        self.format = format

    def load(self, src):
        return src

    def dump(self, src, dst):
        d = self.loader.data.copy()
        d["template_filename"] = src
        fmt = self.format
        if fmt == "raw":
            fmt = "json"
        return loading.dumpfile(d, format=fmt)

    def run(self, src, dst):
        return self.dump(self.load(src), dst)
