import os
import textwrap
import traceback
import linecache
import logging
from collections import defaultdict
from io import StringIO

from .._path import XTemplatePathNotFound, is_physical_path
from .color import highlight
from ._extract import extract_detail, _is_internal_python_frame

logger = logging.getLogger(__name__)


def _display_path(path):
    # package-spec names are not filesystem paths
    if is_physical_path(path):
        return os.path.relpath(path, os.getcwd())
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

    def format(self, d) -> str:
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
    def __init__(self, *, n: int, colorful: bool = False, formatter=None):
        self.n = n
        self.formatter = formatter or Formatter(n, colorful=colorful)

    def render(self, exc: Exception, *, level=None) -> str:
        return self.formatter.format(self.on_error(exc, level=level))

    def on_error(self, exc: Exception, *, level=None) -> dict:
        d = vars(exc).copy()
        detail = extract_detail(exc)
        if detail.jinja2_frames is None:
            if isinstance(exc, XTemplatePathNotFound):
                d.update(_get_info_from_exception(exc))
                return d
            raise exc.with_traceback(exc.__traceback__)

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

            lineno = f.lineno
            filename = f.filename
            print("{}:".format(_display_path(filename)), file=buf)
            start_lineno = max(1, lineno - self.n)
            end_lineno = min(len(linecache.getlines(filename)) + 1, lineno + self.n + 1)
            for i in range(start_lineno, end_lineno):
                line = linecache.getline(filename, lineno=i).rstrip()
                print(self.formatter.line_format(i, line, lineno=lineno), file=buf)

        # python's traceback (e.g. a filter function written in python)
        if detail.python_frames:
            lines = traceback.StackSummary.from_list(detail.python_frames).format()
            print("", file=buf)
            print("Traceback:", file=buf)
            print("".join(lines), file=buf)

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
            d["where"] = _display_path(filename)
        d["output"] = buf.getvalue()
        d.update(_get_info_from_exception(exc))
        return d


# xxx: remove it
def _get_info_from_exception(exc: Exception):
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
    exc: Exception, *, renderer=Renderer, n=3, colorful=False, level=None
) -> str:
    return renderer(n=n, colorful=colorful).render(exc, level=level)
