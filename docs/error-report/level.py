"""Render kamidana's gentle error with an arbitrary frame `level`.

Usage (from a case directory):

    python ../../level.py <template> <level> [-a additionals.py]
"""

import sys

from kamidana.debug import gentleerror
from kamidana.driver import Driver
from kamidana.loader import TemplateLoader


def main():
    template = sys.argv[1]
    level = int(sys.argv[2])
    additionals = []
    if "-a" in sys.argv:
        additionals = [sys.argv[sys.argv.index("-a") + 1]]
    loader = TemplateLoader([], additionals, [])
    driver = Driver(loader, format="raw")
    try:
        driver.run(template, None)
    except Exception as e:
        r = gentleerror.Renderer(n=3)
        d = r.on_error(e, level=level)
        print(r.formatter.format(d), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
