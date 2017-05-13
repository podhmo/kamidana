import jinja2
import sys
from dictknife import loading, deepmerge


def _load_template(filename, encoding="utf-8"):
    with open(filename) as rf:
        return rf.read()  # python3.x only


def run(template_path, data):
    env = jinja2.Environment(
        loader=jinja2.FunctionLoader(_load_template),
        undefined=jinja2.StrictUndefined,
    )
    t = env.get_or_select_template(template_path)
    return t.render(**data)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", action="append", help="support yaml, json, toml", default=[])
    parser.add_argument("template")
    parser.add_argument("--input-format", default=None)
    parser.add_argument("--output-format", default="raw")
    parser.add_argument("--dst", default=None)

    args = parser.parse_args()
    loading.setup()

    data = deepmerge(*[loading.loadfile(d) for d in args.data], override=True)
    if args.input_format is not None:
        data = deepmerge(data, loading.load(sys.stdin, format=args.input_format), override=True)
    result = run(args.template, data)
    loading.dumpfile(result, args.dst, format=args.output_format)
