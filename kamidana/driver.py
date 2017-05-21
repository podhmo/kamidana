import jinja2
from dictknife import loading
from dictknife.langhelpers import reify
from .interfaces import IDriver


def _make_environment(load, additionals):
    env = jinja2.Environment(
        loader=jinja2.FunctionLoader(load),
        undefined=jinja2.StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
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
        return _make_environment(self.loader.load, self.loader.additionals)

    def transform(self, t):
        return t.render(**self.loader.data)

    def load(self, template_file):
        return self.environment.get_or_select_template(template_file)

    def dump(self, d, dst):
        return loading.dumpfile(d, dst, format=self.format)

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
        return loading.dumpfile(d, format=self._detect_output_format())

    def run(self, src, dst):
        return self.dump(self.load(src), dst)

    def _detect_output_format(self):
        if self.format == "raw":
            return "json"
        return self.format
