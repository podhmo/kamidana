import jinja2
from dictknife import loading
from dictknife.langhelpers import reify
from .interfaces import IDriver


def _load_template(filename, encoding="utf-8"):
    with open(filename) as rf:
        return rf.read()  # python3.x only


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
    def __init__(self, data, format, load_template=_load_template, additionals=None):
        self.data = data
        self.format = format
        self.load_template = load_template
        self.additionals = additionals or {}

    @reify
    def environment(self):
        return _make_environment(self.load_template, additionals=self.additionals)

    def transform(self, t):
        return t.render(**self.data)

    def load(self, template_file):
        return self.environment.get_or_select_template(template_file)

    def dump(self, d, dst):
        return loading.dumpfile(d, dst, format=self.format)

    def run(self, src, dst):
        data = self.load(src)
        result = self.transform(data)
        self.dump(result, dst)
