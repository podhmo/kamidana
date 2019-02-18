import sys
import contextlib
from . import gentleerror
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
                gentleerror.translate_error(e, colorful=is_colorful()),
                file=sys.stderr,
            )
        sys.exit(1)
