import sys
import argparse
import logging
from magicalimport import import_symbol
from kamidana.debug import error_handler
from dictknife.loading import get_formats, dumpfile

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
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
    parser.add_argument(
        "-d", "--data", action="append", help="support yaml, json, toml", default=[]
    )
    parser.add_argument(
        "--logging", choices=list(logging._nameToLevel.keys()), default="INFO"
    )
    parser.add_argument("-a", "--additionals", action="append", default=[])
    parser.add_argument("-e", "--extension", action="append", default=[])

    parser.add_argument("-i", "--input-format", default=None, choices=get_formats())
    parser.add_argument("-o", "--output-format", default="raw")
    parser.add_argument(
        "--dump-context",
        action="store_true",
        help="dumping loading data (used by jinja2 template)",
    )
    parser.add_argument(
        "--list-info",
        action="store_true",
        help="listting information (for available extensions and additional modules)",
    )
    parser.add_argument("template", nargs="?")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--dst", default=None)

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

        if args.template is None and not (args.dump_context or args.list_info):
            logger.info("template is not passed, running as --dump-context")
            args.dump_context = True
        if args.dump_context:
            driver_cls = import_symbol("ContextDumpDriver", ns="kamidana.driver")
        elif args.list_info:
            from kamidana import listinfo

            output_format = args.output_format
            if output_format == "raw":
                output_format = "json"
            print(
                "\x1b[1mextensions are used by `-e`, additional modules are used by `-a`.\x1b[0m",
                file=sys.stderr,
            )
            dumpfile(listinfo.listinfo(), format=output_format)
            return print("")
        else:
            driver_cls = import_symbol(args.driver, ns="kamidana.driver")
        driver = driver_cls(loader, format=args.output_format)
        driver.run(args.template, args.dst)
