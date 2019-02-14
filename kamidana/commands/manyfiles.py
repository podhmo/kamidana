import logging
import argparse
from magicalimport import import_symbol
from dictknife.loading import get_formats
from kamidana.debug import error_handler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", action="append", help="support yaml, json, toml", default=[]
    )
    parser.add_argument(
        "--loader",
        default="kamidana.loader:TemplateLoader",
        help="default: kamidana.loader:TemplateLoader",
    )
    parser.add_argument(
        "--logging", choices=list(logging._nameToLevel.keys()), default="INFO"
    )
    parser.add_argument("-a", "--additionals", action="append", default=[])
    parser.add_argument("-e", "--extension", action="append", default=[])
    parser.add_argument("-i", "--input-format", default=None, choices=get_formats())
    parser.add_argument("-o", "--output-format", default="raw")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("batch")
    parser.add_argument("--outdir", default=None)

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    with error_handler(debug=args.debug, quiet=args.quiet):
        loader_cls = import_symbol(args.loader, ns="kamidana.loader")
        extensions = [
            ("jinja2.ext.{}".format(ext) if "." not in ext else ext)
            for ext in args.extension
        ]
        loader = loader_cls(
            args.data, args.additionals, extensions, format=args.input_format
        )
        driver_cls = import_symbol("kamidana.driver:BatchCommandDriver")
        driver = driver_cls(loader, format=args.output_format)
        driver.run(args.batch, args.outdir)
