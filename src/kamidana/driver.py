from __future__ import annotations

import logging
import os.path
import json
import typing as t
import jinja2
from dictknife.deepmerge import deepmerge
from dictknife import loading
from functools import cached_property
from .interfaces import IDriver, ITemplateLoader
from ._path import ResolvingByRelativePathEnvironment

logger = logging.getLogger(__name__)

# "raw" is kamidana's pseudo-format: rendered text is written as-is
# instead of being parsed and re-dumped. dictknife's "raw" loader writes
# a given string verbatim, so the name can be passed to dumpfile as-is.
RAW_FORMAT = "raw"

# the keys a batch command accepts: {"template", "dst"} are required,
# {"data", "format"} are optional
_COMMAND_KEYS = frozenset(["template", "dst", "data", "format"])


def _render_with_newline(tmpl: jinja2.Template, data: t.Mapping[str, t.Any]) -> str:
    r = tmpl.render(**data)
    if r.endswith("\n"):
        return r
    return r + "\n"


def _load_for_dump(rendered: str, fmt: t.Optional[str]) -> t.Any:
    # "raw" writes the rendered text verbatim; any other format parses it
    # back to data so dictknife can re-dump it (e.g. "-o yaml")
    if fmt == RAW_FORMAT:
        return rendered
    return loading.loads(rendered, format=fmt)


def _make_environment(
    load: t.Callable[
        [str], t.Tuple[str, t.Optional[str], t.Optional[t.Callable[[], bool]]]
    ],
    additionals: t.Mapping[str, t.Mapping[str, t.Any]],
    extensions: t.Sequence[str],
    *,
    undefined: t.Optional[t.Type[jinja2.Undefined]] = None,
) -> ResolvingByRelativePathEnvironment:
    env = ResolvingByRelativePathEnvironment(
        loader=jinja2.FunctionLoader(load),
        undefined=undefined or jinja2.StrictUndefined,
        trim_blocks=False,
        lstrip_blocks=True,
        extensions=extensions,
        optimized=False,
    )
    for name, defs in additionals.items():
        getattr(env, name).update(defs)
    return env


class BaseDriver(IDriver):
    undefined: t.Type[jinja2.Undefined] = jinja2.StrictUndefined

    def __init__(self, loader: ITemplateLoader, format: t.Optional[str]) -> None:
        self.loader = loader
        self.format = format

    @cached_property
    def environment(self) -> ResolvingByRelativePathEnvironment:
        return _make_environment(
            self.loader.load,
            self.loader.additionals,
            self.loader.extensions,
            undefined=self.undefined,
        )

    def transform(self, d: t.Any) -> t.Any:
        return d

    def run(self, src: t.Optional[str], dst: t.Optional[str]) -> t.Any:
        return self.dump(self.transform(self.load(src)), dst)


class Driver(BaseDriver):
    def transform(self, tmpl: jinja2.Template) -> str:
        return _render_with_newline(tmpl, self.loader.data)

    def load(self, template_file: t.Optional[str]) -> jinja2.Template:
        # run() is only reached with a template name; onefile.py falls back
        # to --dump-context when no template is given.
        assert template_file is not None
        return self.environment.get_or_select_template(template_file)

    def dump(self, d: str, dst: t.Optional[str]) -> t.Any:
        return loading.dumpfile(
            _load_for_dump(d, self.format),
            t.cast(str, dst),
            format=t.cast(str, self.format),
        )


class ContextDumpDriver(BaseDriver):
    def load(self, src: t.Optional[str]) -> t.Optional[str]:
        return src

    def transform(self, src: t.Optional[str]) -> t.Dict[str, t.Any]:
        d = self.loader.data.copy()
        d["template_filename"] = src
        return d

    def dump(self, d: t.Dict[str, t.Any], dst: t.Optional[str]) -> t.Any:
        # "raw" has no meaning for a context dict; dump it as json
        fmt = "json" if self.format == RAW_FORMAT else self.format
        return loading.dumpfile(d, t.cast(str, dst), format=t.cast(str, fmt))


class BatchCommandDriver(BaseDriver):
    def load(
        self, batch_file: t.Optional[str]
    ) -> t.List[t.Tuple[jinja2.Template, t.Dict[str, t.Any], t.Any]]:
        # "batch" is a required positional argument of kamidana-batch.
        assert batch_file is not None
        commands = loading.loadfile(batch_file)
        if not isinstance(commands, (list, tuple)):
            commands = [commands]

        # core_data comes from the command line (-d/--data) and is merged
        # over each command's own "data": dictknife's "addtoset" merge
        # unions lists and merges dicts recursively, with right-side
        # scalars winning -- so command-line data overrides per-command
        # data on conflicts.
        core_data = self.loader.data
        cache: t.Dict[str, t.Any] = {}
        r: t.List[t.Tuple[jinja2.Template, t.Dict[str, t.Any], t.Any]] = []
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
            tmpl = cache.get(tname)
            if tmpl is None:
                tmpl = cache[tname] = self.environment.get_or_select_template(tname)
            r.append((tmpl, cmd, deepmerge(data, core_data)))
        return r

    def _load_data(self, name_or_data: t.Any, *, cache: t.Dict[str, t.Any]) -> t.Any:
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

    def dump(
        self,
        commands: t.List[t.Tuple[jinja2.Template, t.Dict[str, t.Any], t.Any]],
        outdir: t.Optional[str],
    ) -> None:
        outdir = outdir or "."
        for tmpl, cmd, data in commands:
            result = _render_with_newline(tmpl, data)
            # "dst" is joined under outdir without sanitizing ".."
            # segments, so a command can write outside of outdir.
            # acceptable for a user-run CLI: the batch file is trusted input.
            outpath = os.path.join(outdir, cmd["dst"])
            logger.info("rendering %s (template=%s)", outpath, tmpl.name)
            fmt = cmd.get("format") or self.format or RAW_FORMAT
            loading.dumpfile(_load_for_dump(result, fmt), outpath, format=fmt)
