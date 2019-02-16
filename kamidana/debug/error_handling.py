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


class GentleOutputRenderer:
    def __init__(
        self,
        *,
        n: int,
        full: bool = False,
        formatter=None,
        line_formatter=None,
        colorful: bool = False
    ):
        self.n = n
        self.full = full  # todo: handling (currently, ignored)
        self.colorful = colorful
        # todo: separation
        self.formatter = formatter or self._format
        self.line_formatter = line_formatter or self._line_format

    def _line_format(self, i: int, line: str, *, lineno: int) -> str:
        size = len(str(lineno + self.n))
        text = ("{lineno: %d}: {line}" % (size)).format(lineno=i, line=line)
        if i == lineno:
            return highlight("  -> {}".format(text), colorful=self.colorful)
        return "     {}".format(text)

    def _format(self, d) -> str:
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

    # xxx:
    def is_jinja2_frames(self, frames):
        return "site-packages/jinja2" in frames[-1].filename

    def render(self, exc: Exception) -> str:
        return self.formatter(self.get_information(exc))

    def get_information(self, exc: Exception) -> str:
        return self.on_error(exc)

    def on_error(self, exc: Exception, *, level: int = 5) -> dict:
        # shape :: [python, jinja2, python, ....]
        d = vars(exc).copy()
        detail = extract_detail(exc)
        if not detail.jinja2:
            if isinstance(exc, XTemplatePathNotFound):
                d.update(_get_info_from_exception(exc))
                return d
            raise exc.with_traceback(exc.__traceback__)

        logger.debug(
            "frame shape: %r", [(fs.kind, len(fs.frames)) for fs in detail.framesets]
        )

        buf = StringIO()
        first = True
        # jinja2's traceback
        for i in reversed(range(1, min(level, len(detail.jinja2.frames) + 1))):
            if first:
                first = False
            else:
                print("", file=buf)

            lineno = detail.jinja2.frames[-i].lineno
            filename = detail.jinja2.frames[-i].filename
            print("{}:".format(os.path.relpath(filename, os.getcwd())), file=buf)
            start_lineno = max(1, lineno - self.n)
            end_lineno = min(len(linecache.getlines(filename)) + 1, lineno + self.n + 1)
            for i in range(start_lineno, end_lineno):
                line = linecache.getline(filename, lineno=i).rstrip()
                print(self.line_formatter(i, line, lineno=lineno), file=buf)

        # python's traceback
        if not detail.outermost:
            frames = detail.framesets[-1].frames
            if not self.is_jinja2_frames(frames):
                lines = traceback.StackSummary.from_list(frames).format()
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


def get_gentle_output_from_exception(
    exc: jinja2.TemplateError,
    *,
    renderer=GentleOutputRenderer,
    full=False,
    n=3,
    colorful=False
) -> str:
    return renderer(full=full, n=n, colorful=colorful).render(exc)
