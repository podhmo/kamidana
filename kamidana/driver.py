import logging
import os.path
import json
import jinja2
import jinja2.ext as ext
from dictknife import deepmerge
from dictknife import loading
from dictknife.langhelpers import reify
from .interfaces import IDriver
logger = logging.getLogger(__name__)


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
        template = self.load(src)
        result = self.transform(template)
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

    def _detect_output_format(self):
        if self.format == "raw":
            return "json"
        return self.format


class BatchCommandDriver(IDriver):
    def __init__(self, loader, format):
        self.loader = loader
        self.format = format
        self.cache = {}

    @reify
    def environment(self):
        return _make_environment(self.loader.load, self.loader.additionals)

    def load(self, batch_file):
        commands = loading.loadfile(batch_file)
        if not isinstance(commands, (list, tuple)):
            commands = [commands]

        core_data = self.loader.data
        cache = {}
        r = []
        for cmd in commands:
            # require: template, outfile
            for name in ["template", "outfile"]:
                if name not in cmd:
                    raise RuntimeError(
                        "{} is missing. this is required field. (passed command={})".
                        format(name, json.dumps(cmd, ensure_ascii=False))
                    )

            data = self._load_data(cmd.get("data"), cache=cache)
            tname = cmd["template"]
            t = cache.get(tname)
            if t is None:
                t = cache[tname] = self.environment.get_or_select_template(tname)
            r.append((t, cmd, deepmerge(data, core_data)))
        return r

    def _load_data(self, name_or_data, *, cache):
        if name_or_data is None:
            return {}
        elif isinstance(name_or_data, (list, tuple)):
            return deepmerge(*[self._load_data(d, cache=cache) for d in name_or_data])
        elif hasattr(name_or_data, "get"):
            return name_or_data
        else:
            r = cache.get(name_or_data)
            if r is None:
                r = cache[name_or_data] = loading.loadfile(name_or_data)
            return r

    def dump(self, commands, outdir):
        outdir = outdir or "."
        for t, cmd, data in commands:
            result = t.render(**data)
            outpath = os.path.join(outdir, cmd["outfile"])
            logger.info("out: %s", outpath)
            loading.dumpfile(result, outpath, format=self.format)

    def run(self, batch_file, outdir):
        return self.dump(self.load(batch_file), outdir)
