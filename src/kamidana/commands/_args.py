from __future__ import annotations

import argparse
import logging
from typing import TYPE_CHECKING

import jinja2
from dictknife.loading import get_formats

from kamidana._import import import_symbol

if TYPE_CHECKING:
    import typing as t

    from kamidana.interfaces import IDriver, ITemplateLoader


def make_common_parser() -> argparse.ArgumentParser:
    """the option set shared by the kamidana and kamidana-batch commands."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--loader",
        default="kamidana.loader:TemplateLoader",
        help="default: kamidana.loader:TemplateLoader",
    )
    parser.add_argument(
        "-d", "--data", action="append", help="support yaml, json, toml", default=[]
    )
    # logging._nameToLevel is private; getLevelNamesMapping() replaces it on 3.11+
    parser.add_argument(
        "--logging", choices=list(logging._nameToLevel.keys()), default="INFO"
    )
    parser.add_argument("-a", "--additionals", action="append", default=[])
    parser.add_argument("-e", "--extension", action="append", default=[])
    parser.add_argument("-i", "--input-format", default=None, choices=get_formats())
    parser.add_argument("-o", "--output-format", default="raw")
    parser.add_argument(
        "--strict-undefined",
        action="store_true",
        help="raise an error when an undefined variable is used (jinja2.StrictUndefined)",
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    return parser


def setup_logging(args: argparse.Namespace) -> None:
    logging.basicConfig(level=getattr(logging, args.logging))


def build_loader(args: argparse.Namespace) -> ITemplateLoader:
    """resolve --loader and build the template loader."""
    loader_cls = import_symbol(args.loader, ns="kamidana.loader", cwd=True)
    extensions = [
        ("jinja2.ext.{}".format(ext) if "." not in ext else ext)
        for ext in args.extension
    ]
    loader: ITemplateLoader = loader_cls(
        args.data, args.additionals, extensions, format=args.input_format
    )
    return loader


def build_driver(
    driver_cls: t.Callable[..., IDriver],
    loader: ITemplateLoader,
    args: argparse.Namespace,
) -> IDriver:
    driver = driver_cls(loader, format=args.output_format)
    if args.strict_undefined:
        driver.undefined = jinja2.StrictUndefined
    return driver
