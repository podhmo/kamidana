"""Render a template with plain jinja2 (no kamidana), printing the raw traceback.

Usage (from a case directory):

    python ../j2.py <template-name>

If ``additionals.py`` exists in the current directory, functions marked with
kamidana's ``as_filter``/``as_global``/``as_test`` decorators are registered,
so the same templates can be rendered by both commands.
"""

import os.path
import sys
import traceback

import jinja2


def main():
    template_name = sys.argv[1]
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("."),
        undefined=jinja2.StrictUndefined,
        trim_blocks=False,
        lstrip_blocks=True,
        optimized=False,
    )
    if os.path.exists("additionals.py"):
        sys.path.insert(0, os.getcwd())
        import additionals

        from kamidana import collect_marked_items

        for name, defs in collect_marked_items(additionals).items():
            getattr(env, name).update(defs)
    t = env.get_template(template_name)
    sys.stdout.write(t.render())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
