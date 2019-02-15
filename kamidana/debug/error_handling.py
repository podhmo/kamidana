import os
import textwrap
import traceback
from collections import defaultdict
from io import StringIO
import jinja2
from .._path import XTemplatePathNotFound
from .color import highlight


def _get_info_from_exception(exc: jinja2.TemplateError):
    d = {
        "exc_class": "{}.{}".format(exc.__module__, exc.__class__.__name__),
        "message": str(exc),
    }

    if hasattr(exc, "filename"):
        d["where"] = exc.filename or exc.name
        return d

    # hack: original expression from hidden api
    if hasattr(exc, "original_context"):
        octx = exc.original_context
        if octx.where is not None:
            d["where"] = os.path.relpath(octx.where, os.getcwd())
        d["message"] = d["message"].replace(exc.args[0], octx.path)
    return d


class GentleOutputRenderer:
    def __init__(
        self, *, n: int, full: bool = False, formatter=None, colorful: bool = False
    ):
        self.n = n
        self.full = full  # todo: handling (currently, ignored)
        self.formatter = formatter or self._format
        self.colorful = colorful

    def _format(self, d):
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

    def render(self, exc: Exception) -> str:
        return self.formatter(self.get_information(exc))

    def get_information(self, exc: Exception) -> str:
        if isinstance(exc, jinja2.TemplateSyntaxError):
            return self.on_syntax_error(exc)
        elif isinstance(exc, (XTemplatePathNotFound, jinja2.TemplateError)):
            return self.on_template_error(exc)
        else:
            raise

    def on_template_error(self, exc: jinja2.TemplateError) -> dict:
        d = vars(exc).copy()
        d.update(_get_info_from_exception(exc))
        d["output"] = traceback.format_exc(limit=3)
        return d

    def on_syntax_error(self, exc: jinja2.TemplateSyntaxError) -> dict:
        d = vars(exc).copy()
        lineno = exc.lineno  # int
        # name = exc.name  # Optional[str]
        # filename = exc.filename  # Optional[str]
        source = exc.source  # str
        # translated = exc.translated  # bool

        buf = StringIO()
        lines = source.split("\n")
        start_position = max(0, lineno - 1 - self.n)
        end_position = min(len(lines), lineno + self.n)

        for i, line in enumerate(
            lines[start_position:end_position], start_position + 1
        ):
            size = len(str(lineno + self.n))
            text = ("{lineno: %d}: {line}" % (size)).format(lineno=i, line=line)
            if i == lineno:
                print(highlight("-> {}".format(text), colorful=self.colorful), file=buf)
            else:
                print("   {}".format(text), file=buf)

        d["output"] = buf.getvalue()
        d.update(_get_info_from_exception(exc))
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
