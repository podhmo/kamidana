"""
Naming helpers (e.g. snakecase, kebabcase, ... pluralize, singularize)
"""
from __future__ import annotations

import re
import inflection
from kamidana import as_filter

pluralize = as_filter(inflection.pluralize)
singularize = as_filter(inflection.singularize)


@as_filter
def snakecase(
    name: str,
    rx0: re.Pattern[str] = re.compile("(.)([A-Z][a-z]+)"),
    rx1: re.Pattern[str] = re.compile("([a-z0-9])([A-Z])"),
    rx2: re.Pattern[str] = re.compile("[A-Z]+"),
    separator: str = "_",
    from_separator: str = "-",
) -> str:
    if from_separator in name:
        if rx2.search(name) is None:
            return name.replace(from_separator, separator)
        else:
            return separator.join(
                snakecase(x, separator=separator, from_separator=from_separator)
                for x in name.split(from_separator)
            )
    m = rx2.match(name)
    if m is not None:
        i = m.end()
        return separator.join(
            [
                name[:i].lower(),
                snakecase(name[i:], separator=separator, from_separator=from_separator),
            ]
        )
    else:
        pattern = r"\1{}\2".format(separator)
        return rx1.sub(pattern, rx0.sub(pattern, name)).lower()


@as_filter
def kebabcase(name: str) -> str:
    return snakecase(name, separator="-", from_separator="_")


@as_filter
def lispcase(name: str) -> str:  # alias
    return snakecase(name, separator="-", from_separator="_")


@as_filter
def camelcase(name: str) -> str:
    return untitleize(pascalcase(name))


@as_filter
def pascalcase(name: str, rx: re.Pattern[str] = re.compile(r"[\-_ ]")) -> str:
    return "".join(titleize(x) for x in rx.split(name))


@as_filter
def titleize(name: str) -> str:
    if not name:
        return name
    name = str(name)
    return "{}{}".format(name[0].upper(), name[1:])


@as_filter
def untitleize(name: str) -> str:
    if not name:
        return name
    return "{}{}".format(name[0].lower(), name[1:])
