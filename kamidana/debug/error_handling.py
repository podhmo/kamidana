import jinja2
import textwrap
import traceback
from collections import defaultdict
from io import StringIO


def _get_jinja2_exception_info(exc: jinja2.TemplateError):
    return {
        "exception_class": "{}.{}".format(exc.__module__, exc.__class__.__name__),
        "exception_message": str(exc),
    }


class GentleOutputRenderer:
    def __init__(
        self, *, n: int, full: bool = False, formatter=None, title="Error Report"
    ):
        self.title = title
        self.n = n
        self.full = full  # todo: handling (currently, ignored)
        self.formatter = formatter or self._format

    def _format(self, d):
        d = defaultdict(lambda: None, d)
        fmt = textwrap.dedent(
            """
            {title}
            ------------------------------------------------------------
            exception: {d[exception_class]}
            message: {d[exception_message]}
            where: {d[filename]}
            ------------------------------------------------------------
            """
        )
        fmt2 = textwrap.dedent(
            """
            {d[output]}
            """
        )
        if "output" in d:
            fmt += fmt2.strip("\n")
        return fmt.format(d=d, title=self.title)

    def render(self, exc: Exception) -> str:
        return self.formatter(self.get_output(exc))

    def get_output(self, exc: Exception) -> str:
        if isinstance(exc, jinja2.TemplateSyntaxError):
            return self.on_syntax_error(exc)
        elif isinstance(exc, jinja2.TemplateError):
            return self.on_template_error(exc)
        else:
            raise

    def on_template_error(self, exc: jinja2.TemplateError) -> dict:
        d = vars(exc).copy()
        d.update(_get_jinja2_exception_info(exc))
        d["output"] = traceback.format_exc()
        return d

    def on_syntax_error(self, exc: jinja2.TemplateSyntaxError) -> dict:
        # todo: bold
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
            if i == lineno:
                cursor = "->"
            else:
                cursor = "  "

            size = len(str(lineno + self.n))
            fmt = "{cursor} {lineno: %d}: {line}" % (size)
            print(fmt.format(cursor=cursor, lineno=i, line=line), file=buf)

        d["output"] = buf.getvalue()
        d.update(_get_jinja2_exception_info(exc))
        return d


def get_gentle_output_from_exception(
    exc: jinja2.TemplateError, *, renderer=GentleOutputRenderer, full=False, n=3
) -> str:
    return renderer(full=full, n=n).render(exc)
