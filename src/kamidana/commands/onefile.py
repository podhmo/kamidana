import sys
import logging
from kamidana._import import import_symbol
from kamidana.debug import error_handler, is_colorful
from dictknife.loading import dumpfile
from ._args import make_common_parser, setup_logging, build_loader, build_driver

logger = logging.getLogger(__name__)


def main() -> None:
    parser = make_common_parser()
    parser.add_argument(
        "--driver",
        default="kamidana.driver:Driver",
        help="default: kamidana.driver:Driver",
    )
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
    parser.add_argument(
        "template",
        nargs="?",
        help="template file ('./foo.j2', '../foo.j2', '/foo.j2') or a template"
        " in a python package ('<package>/<path>')",
    )
    parser.add_argument("--dst", default=None)

    args = parser.parse_args()
    setup_logging(args)

    with error_handler(debug=args.debug, quiet=args.quiet):
        loader = build_loader(args)

        if args.template is None and not (args.dump_context or args.list_info):
            logger.info("template is not passed, running as --dump-context")
            args.dump_context = True
        if args.dump_context:
            driver_cls = import_symbol("ContextDumpDriver", ns="kamidana.driver", cwd=True)
        elif args.list_info:
            from kamidana import listinfo

            output_format = args.output_format
            if output_format == "raw":
                output_format = "json"
            header = (
                "extensions are used by `-e`, additional modules are used by `-a`."
            )
            if is_colorful():
                header = "\x1b[1m{}\x1b[0m".format(header)
            print(header, file=sys.stderr)
            dumpfile(listinfo.listinfo(), format=output_format)
            return print("")
        else:
            driver_cls = import_symbol(args.driver, ns="kamidana.driver", cwd=True)
        driver = build_driver(driver_cls, loader, args)
        driver.run(args.template, args.dst)
