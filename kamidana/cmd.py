import sys
from magicalimport import import_symbol, import_module
from dictknife import loading, deepmerge
from kamidana import collect_marked_items


def load_data(data_pathset, format=None):
    data = deepmerge(*[loading.loadfile(d) for d in data_pathset], override=True)
    if format is not None:
        data = deepmerge(data, loading.load(sys.stdin, format=format), override=True)
    return data


def load_additionals(path):
    if path is None:
        return {}
    m = import_module(path)
    return collect_marked_items(m)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", action="append", help="support yaml, json, toml", default=[])
    parser.add_argument("--driver", default="kamidana.driver:Driver")
    parser.add_argument("--data-loader", default="kamidana.cmd:load_data")
    parser.add_argument("--additionals", default=None)
    parser.add_argument("--input-format", default=None)
    parser.add_argument("--output-format", default="raw")
    parser.add_argument("template")
    parser.add_argument("--dst", default=None)

    args = parser.parse_args()
    loading.setup()

    load_data = import_symbol(args.data_loader, ns="kamidana.cmd")
    data = load_data(args.data, format=args.input_format)

    additionals = load_additionals(args.additionals)

    driver_cls = import_symbol(args.driver, ns="kamidana.driver")
    driver = driver_cls(data, format=args.output_format, additionals=additionals)
    driver.run(args.template, args.dst)
