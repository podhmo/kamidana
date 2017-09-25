import logging
import argparse
from magicalimport import import_symbol


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", action="append", help="support yaml, json, toml", default=[])
    parser.add_argument(
        "--loader",
        default="kamidana.loader:TemplateLoader",
        help="default: kamidana.loader:TemplateLoader",
    )
    parser.add_argument("--additionals", default=None)
    parser.add_argument("-i", "--input-format", default=None)
    parser.add_argument("-o", "--output-format", default="raw")
    parser.add_argument("batch")
    parser.add_argument("--outdir", default=None)

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    loader_cls = import_symbol(args.loader, ns="kamidana.loader")
    loader = loader_cls(args.data, args.additionals, args.input_format)
    driver_cls = import_symbol("kamidana.driver:BatchCommandDriver")
    driver = driver_cls(loader, format=args.output_format)
    driver.run(args.batch, args.outdir)
