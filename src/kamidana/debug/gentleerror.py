from __future__ import annotations

import os
import textwrap
import traceback
import linecache
import logging
from collections import defaultdict
from io import StringIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import typing as t

from .._path import XTemplatePathNotFound, is_physical_path
from .color import highlight
from ._extract import extract_detail, _is_internal_python_frame

logger = logging.getLogger(__name__)


def _display_path(path: str) -> str:
    # package-spec names are not filesystem paths
    if is_physical_path(path):
        # shorten paths inside the current directory; outside it a
        # "../.."-laden relpath is worse than the absolute spelling
        relpath = os.path.relpath(path, os.getcwd())
        if not relpath.startswith(".."):
            return relpath
    return path


class Formatter:
    def __init__(self, n: int, *, colorful: bool = False):
        self.n = n
        self.colorful = colorful

    def line_format(self, i: int, line: str, *, lineno: int) -> str:
        size = len(str(lineno + self.n))
        text = ("{lineno: %d}: {line}" % (size)).format(lineno=i, line=line)
        if i == lineno:
            return highlight("  -> {}".format(text), colorful=self.colorful)
        return "     {}".format(text)

    def format(self, d: t.Mapping[str, t.Any]) -> str:
        d = defaultdict(lambda: None, d)
        fmt = textwrap.dedent(
            """
            ------------------------------------------------------------
            exception: {d[exc_class]}
            message: {d[message]}
            ------------------------------------------------------------
            """.lstrip(
                "\n"
            )
        )
        if d["where"] is not None:
            fmt = fmt.replace(
                "message: {d[message]}\n",
                "message: {d[message]}\nwhere: {d[where]}\n",
            )
        fmt2 = textwrap.dedent(
            """
            {d[output]}
            """.strip(
                "\n"
            )
        )
        if "output" in d:
            fmt += fmt2
        return fmt.format(d=d).rstrip()


class Renderer:
    def __init__(
        self,
        *,
        n: int,
        colorful: bool = False,
        formatter: t.Optional[Formatter] = None,
    ) -> None:
        self.n = n
        self.formatter = formatter or Formatter(n, colorful=colorful)

    def render(self, exc: Exception, *, level: t.Optional[int] = None) -> str:
        return self.formatter.format(self.on_error(exc, level=level))

    def on_error(
        self, exc: Exception, *, level: t.Optional[int] = None
    ) -> t.Dict[str, t.Any]:
        d = vars(exc).copy()
        detail = extract_detail(exc)
        if detail.jinja2_frames is None:
            if isinstance(exc, XTemplatePathNotFound):
                d.update(_get_info_from_exception(exc))
                return d
            return self._on_python_error(exc, d)

        logger.debug("jinja2 frames: %r", detail.jinja2_frames)

        frames = detail.jinja2_frames  # outermost -> innermost
        n_omitted = 0
        if level is not None and len(frames) > level > 0:
            n_omitted = len(frames) - level
            frames = frames[n_omitted:]

        buf = StringIO()
        if n_omitted:
            print("... ({} frames omitted)".format(n_omitted), file=buf)
            print("", file=buf)
        first = True
        for f in frames:
            if first:
                first = False
            else:
                print("", file=buf)
            self._print_frame_context(buf, f)

        # python's traceback (e.g. a filter function written in python)
        if detail.python_frames:
            print("", file=buf)
            print("Traceback:", file=buf)
            print(_format_traceback(detail.python_frames), file=buf, end="")

        # the raise site is the innermost python frame, unless it sits
        # inside stdlib/jinja2/kamidana internals the user cannot act on
        # (e.g. a RecursionError raised in frozen posixpath)
        actionable = [
            f for f in detail.python_frames if not _is_internal_python_frame(f)
        ]
        if actionable:
            f = actionable[-1]
            d["where"] = "{}:{}".format(_display_path(f.filename), f.lineno)
        else:
            d["where"] = _display_path(frames[-1].filename)
        d["output"] = buf.getvalue()
        d.update(_get_info_from_exception(exc))
        return d

    def _print_frame_context(
        self, buf: StringIO, f: traceback.FrameSummary
    ) -> None:
        if f.lineno is None:
            return
        lineno = f.lineno
        filename = f.filename
        print("{}:".format(_display_path(filename)), file=buf)
        start_lineno = max(1, lineno - self.n)
        end_lineno = min(len(linecache.getlines(filename)) + 1, lineno + self.n + 1)
        for i in range(start_lineno, end_lineno):
            line = linecache.getline(filename, lineno=i).rstrip()
            print(self.formatter.line_format(i, line, lineno=lineno), file=buf)

    def _on_python_error(
        self, exc: Exception, d: t.Dict[str, t.Any]
    ) -> t.Dict[str, t.Any]:
        # no template frames: a plain python error (e.g. an additional
        # module that failed while being imported).  the same
        # exception/message/where block is rendered, pointing at the
        # innermost frame the user can act on.
        frames = (
            traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
        )
        actionable = [f for f in frames if not _is_internal_python_frame(f)]

        buf = StringIO()
        if actionable:
            innermost = actionable[-1]
            if innermost.lineno is not None:
                self._print_frame_context(buf, innermost)
                print("", file=buf)
            d["where"] = "{}:{}".format(
                _display_path(innermost.filename), innermost.lineno
            )

        shown = actionable or frames
        if shown:
            print("Traceback:", file=buf)
            print(_format_traceback(shown), file=buf, end="")

        d["output"] = buf.getvalue()
        d.update(_get_info_from_exception(exc))
        return d


def _format_traceback(frames: t.List[traceback.FrameSummary]) -> str:
    # like StackSummary.format() but with display-relative filenames
    lines = []
    for fs in frames:
        lines.append(
            '  File "{}", line {}, in {}\n'.format(
                _display_path(fs.filename), fs.lineno, fs.name
            )
        )
        if fs.line:
            lines.append("    {}\n".format(fs.line.strip()))
    return "".join(lines)


# xxx: remove it
def _get_info_from_exception(exc: Exception) -> t.Dict[str, t.Any]:
    d = {
        "exc_class": "{}.{}".format(
            getattr(exc, "__module__", "builtins"), exc.__class__.__name__
        ),
        "message": str(exc),
    }
    # hack: original expression from hidden api
    if hasattr(exc, "original_context"):
        octx = exc.original_context
        if octx.where is not None:
            d["where"] = _display_path(octx.where)
        d["message"] = d["message"].replace(exc.args[0], octx.path)
    return d


def translate_error(
    exc: Exception,
    *,
    renderer: t.Type[Renderer] = Renderer,
    n: int = 3,
    colorful: bool = False,
    level: t.Optional[int] = None,
) -> str:
    return renderer(n=n, colorful=colorful).render(exc, level=level)
