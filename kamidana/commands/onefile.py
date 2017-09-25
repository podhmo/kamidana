import argparse
from magicalimport import import_symbol


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", action="append", help="support yaml, json, toml", default=[])
    parser.add_argument(
        "--driver",
        default="kamidana.driver:Driver",
        help="default: kamidana.driver:Driver",
    )
    parser.add_argument(
        "--loader",
        default="kamidana.loader:TemplateLoader",
        help="default: kamidana.loader:TemplateLoader",
    )
    parser.add_argument("--additionals", default=None)
    parser.add_argument("-i", "--input-format", default=None)
    parser.add_argument("-o", "--output-format", default="raw")
    parser.add_argument("--dump-context", action="store_true")
    parser.add_argument("template")
    parser.add_argument("--dst", default=None)

    args = parser.parse_args()

    loader_cls = import_symbol(args.loader, ns="kamidana.loader")
    loader = loader_cls(args.data, args.additionals, args.input_format)

    if args.dump_context:
        driver_cls = import_symbol("ContextDumpDriver", ns="kamidana.driver")
    else:
        driver_cls = import_symbol(args.driver, ns="kamidana.driver")
    driver = driver_cls(loader, format=args.output_format)
    driver.run(args.template, args.dst)
