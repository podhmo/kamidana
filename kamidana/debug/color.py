import sys


def is_colorful(*, colorful=None) -> bool:
    return colorful or (colorful is None and sys.stdout.isatty())


def highlight(content: str, *, colorful: bool) -> str:
    if not colorful:
        return content
    return "\x1b[33m\x1b[1m{}\x1b[0m".format(content)
