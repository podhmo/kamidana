from __future__ import annotations

import sys
import contextlib
from typing import TYPE_CHECKING
from . import gentleerror
from .color import is_colorful, highlight

if TYPE_CHECKING:
    import typing as t

__all__ = ["error_handler", "gentleerror", "highlight", "is_colorful"]


@contextlib.contextmanager
def error_handler(*, quiet: bool, debug: bool) -> t.Iterator[None]:
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
