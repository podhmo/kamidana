from __future__ import annotations

from kamidana._import import import_symbol
from kamidana.debug import error_handler
from ._args import make_common_parser, setup_logging, build_loader, build_driver


def main() -> None:
    parser = make_common_parser()
    parser.add_argument(
        "batch",
        help="batch file. 'template' in each command accepts a file"
        " ('./foo.j2', '../foo.j2', '/foo.j2') or a template in a python"
        " package ('<package>/<path>')",
    )
    parser.add_argument("--outdir", default=None)

    args = parser.parse_args()
    setup_logging(args)

    with error_handler(debug=args.debug, quiet=args.quiet):
        loader = build_loader(args)
        driver_cls = import_symbol("kamidana.driver:BatchCommandDriver", cwd=True)
        driver = build_driver(driver_cls, loader, args)
        driver.run(args.batch, args.outdir)
