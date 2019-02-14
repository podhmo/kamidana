import sys
import contextlib
from .error_handling import get_gentle_output_from_exception  # noqa
from .color import is_colorful, highlight


@contextlib.contextmanager
def error_handler(*, quiet: bool, debug: bool):
    try:
        yield
    except Exception as e:
        if debug:
            raise
        if quiet:
            message = "{e.__class__.__name__}: {e}".format(e=e)
            print(highlight(message, colorful=is_colorful()), file=sys.stderr)
        else:
            print(
                get_gentle_output_from_exception(e, colorful=is_colorful()),
                file=sys.stderr,
            )
        sys.exit(1)
