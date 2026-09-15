import os
import textwrap
import traceback
import linecache
import logging
from collections import defaultdict
from io import StringIO

import jinja2

from .._path import XTemplatePathNotFound
from .color import highlight
from ._extract import extract_detail

logger = logging.getLogger(__name__)


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
            where: {d[where]}
            ------------------------------------------------------------
            """.lstrip(
                "\n"
            )
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

    def render(self, exc: Exception) -> str:
        return self.formatter.format(self.on_error(exc))

    def on_error(self, exc: Exception, *, level: int = 5) -> dict:
        d = vars(exc).copy()
        detail = extract_detail(exc)
        if detail.jinja2_frames is None:
            if isinstance(exc, XTemplatePathNotFound):
                d.update(_get_info_from_exception(exc))
                return d
            raise exc.with_traceback(exc.__traceback__)

        logger.debug("jinja2 frames: %r", detail.jinja2_frames)

        buf = StringIO()
        first = True
        for f in detail.jinja2_frames[-level:]:  # outermost -> innermost
            if first:
                first = False
            else:
                print("", file=buf)

            lineno = f.lineno
            filename = f.filename
            print("{}:".format(os.path.relpath(filename, os.getcwd())), file=buf)
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

        d["where"] = os.path.relpath(filename, start=os.getcwd())  # xxx
        d["output"] = buf.getvalue()
        d.update(_get_info_from_exception(exc))
        return d


# xxx: remove it
def _get_info_from_exception(exc: jinja2.TemplateError):
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
            d["where"] = os.path.relpath(octx.where, os.getcwd())
        d["message"] = d["message"].replace(exc.args[0], octx.path)
    return d


def translate_error(exc: Exception, *, renderer=Renderer, n=3, colorful=False) -> str:
    return renderer(n=n, colorful=colorful).render(exc)
