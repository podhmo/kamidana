from magicalimport import import_symbol
from dictknife import loading


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", action="append", help="support yaml, json, toml", default=[])
    parser.add_argument("--driver", default="kamidana.driver:Driver", help="default: kamidana.driver:Driver")
    parser.add_argument("--loader", default="kamidana.loader:Loader", help="default: kamidana.loader:Loader")
    parser.add_argument("--additionals", default=None)
    parser.add_argument("--input-format", default=None)
    parser.add_argument("--output-format", default="raw")
    parser.add_argument("template")
    parser.add_argument("--dst", default=None)

    args = parser.parse_args()
    loading.setup()

    loader_cls = import_symbol(args.loader, ns="kamidana.loader")
    loader = loader_cls(args.data, args.additionals, args.input_format)

    driver_cls = import_symbol(args.driver, ns="kamidana.driver")
    driver = driver_cls(loader, format=args.output_format)
    driver.run(args.template, args.dst)
