import jinja2
from dictknife import loading
from dictknife.langhelpers import reify


def _load_template(filename, encoding="utf-8"):
    with open(filename) as rf:
        return rf.read()  # python3.x only


class Driver:
    def __init__(self, data, format, load_template=_load_template):
        self.data = data
        self.format = format
        self.load_template = load_template

    @reify
    def environment(self):
        return jinja2.Environment(
            loader=jinja2.FunctionLoader(self.load_template),
            undefined=jinja2.StrictUndefined,
        )

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
