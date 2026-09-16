import logging
import os.path
import json
import jinja2
from dictknife import deepmerge
from dictknife import loading
from dictknife.langhelpers import reify
from .interfaces import IDriver
from ._path import ResolvingByRelativePathEnvironment

logger = logging.getLogger(__name__)

# "raw" is kamidana's pseudo-format: rendered text is written as-is
# instead of being parsed and re-dumped. dictknife's "raw" loader writes
# a given string verbatim, so the name can be passed to dumpfile as-is.
RAW_FORMAT = "raw"

# the keys a batch command accepts: {"template", "dst"} are required,
# {"data", "format"} are optional
_COMMAND_KEYS = frozenset(["template", "dst", "data", "format"])


def _render_with_newline(t, data):
    r = t.render(**data)
    if r.endswith("\n"):
        return r
    return r + "\n"


def _load_for_dump(rendered, fmt):
    # "raw" writes the rendered text verbatim; any other format parses it
    # back to data so dictknife can re-dump it (e.g. "-o yaml")
    if fmt == RAW_FORMAT:
        return rendered
    return loading.loads(rendered, format=fmt)


def _make_environment(load, additionals, extensions, *, undefined=None):
    env = ResolvingByRelativePathEnvironment(
        loader=jinja2.FunctionLoader(load),
        undefined=undefined or jinja2.Undefined,
        trim_blocks=False,
        lstrip_blocks=True,
        extensions=extensions,
        optimized=False,
    )
    for name, defs in additionals.items():
        getattr(env, name).update(defs)
    return env


class BaseDriver(IDriver):
    undefined = jinja2.Undefined

    def __init__(self, loader, format):
        self.loader = loader
        self.format = format

    @reify
    def environment(self):
        return _make_environment(
            self.loader.load,
            self.loader.additionals,
            self.loader.extensions,
            undefined=self.undefined,
        )

    def transform(self, t):
        return t

    def run(self, src, dst):
        return self.dump(self.transform(self.load(src)), dst)


class Driver(BaseDriver):
    def transform(self, t):
        return _render_with_newline(t, self.loader.data)

    def load(self, template_file):
        return self.environment.get_or_select_template(template_file)

    def dump(self, d, dst):
        return loading.dumpfile(
            _load_for_dump(d, self.format), dst, format=self.format
        )


class ContextDumpDriver(BaseDriver):
    def load(self, src):
        return src

    def transform(self, src):
        d = self.loader.data.copy()
        d["template_filename"] = src
        return d

    def dump(self, d, dst):
        # "raw" has no meaning for a context dict; dump it as json
        fmt = "json" if self.format == RAW_FORMAT else self.format
        return loading.dumpfile(d, dst, format=fmt)


class BatchCommandDriver(BaseDriver):
    def load(self, batch_file):
        commands = loading.loadfile(batch_file)
        if not isinstance(commands, (list, tuple)):
            commands = [commands]

        # core_data comes from the command line (-d/--data) and is merged
        # over each command's own "data": dictknife's "addtoset" merge
        # unions lists and merges dicts recursively, with right-side
        # scalars winning -- so command-line data overrides per-command
        # data on conflicts.
        core_data = self.loader.data
        cache = {}
        r = []
        for cmd in commands:
            if not isinstance(cmd, dict):
                raise RuntimeError(
                    "a batch command must be a mapping. (passed command={})".format(
                        json.dumps(cmd, ensure_ascii=False)
                    )
                )
            unknown = set(cmd) - _COMMAND_KEYS
            if unknown:
                logger.warning(
                    "batch command has unknown keys %s, ignoring them. (command=%s)",
                    sorted(unknown),
                    json.dumps(cmd, ensure_ascii=False),
                )
            for name in ["template", "dst"]:
                if name not in cmd:
                    raise RuntimeError(
                        "{} is missing. this is required field. (passed command={})".format(
                            name, json.dumps(cmd, ensure_ascii=False)
                        )
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
            result = _render_with_newline(t, data)
            # "dst" is joined under outdir without sanitizing ".."
            # segments, so a command can write outside of outdir.
            # acceptable for a user-run CLI: the batch file is trusted input.
            outpath = os.path.join(outdir, cmd["dst"])
            logger.info("rendering %s (template=%s)", outpath, t.name)
            fmt = cmd.get("format") or self.format or RAW_FORMAT
            loading.dumpfile(_load_for_dump(result, fmt), outpath, format=fmt)
