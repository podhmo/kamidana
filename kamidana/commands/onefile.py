import argparse
import logging
from magicalimport import import_symbol
from dictknife.langhelpers import traceback_shortly

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
    parser.add_argument("--logging", choices=list(logging._nameToLevel.keys()), default="INFO")
    parser.add_argument("-a", "--additionals", action="append", default=[])
    parser.add_argument("-e", "--extension", action="append", default=[])
    parser.add_argument("-i", "--input-format", default=None)
    parser.add_argument("-o", "--output-format", default="raw")
    parser.add_argument("--dump-context", action="store_true")
    parser.add_argument("template", nargs="?")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--dst", default=None)

    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))

    with traceback_shortly(args.debug):
        loader_cls = import_symbol(args.loader, ns="kamidana.loader")
        extensions = [
            ("jinja2.ext.{}".format(ext) if "." not in ext else ext) for ext in args.extension
        ]
        loader = loader_cls(args.data, args.additionals, extensions, format=args.input_format)

        if args.template is None:
            logger.info("template is not passed, running as --dump-context")
            args.dump_context = True
        if args.dump_context:
            driver_cls = import_symbol("ContextDumpDriver", ns="kamidana.driver")
        else:
            driver_cls = import_symbol(args.driver, ns="kamidana.driver")
        driver = driver_cls(loader, format=args.output_format)
        driver.run(args.template, args.dst)
