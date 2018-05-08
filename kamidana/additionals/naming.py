from functools import partial
import re
import inflection
from kamidana import as_filter
from jinja2.filters import contextfilter

pluralize = as_filter(contextfilter(inflection.pluralize))
singularize = as_filter(contextfilter(inflection.singularize))


@as_filter
@contextfilter
def snakecase(
    name, rx0=re.compile('(.)([A-Z][a-z]+)'), rx1=re.compile('([a-z0-9])([A-Z])'), separator="_"
):
    pattern = r'\1{}\2'.format(separator)
    return rx1.sub(pattern, rx0.sub(pattern, name)).lower()


lispcase = as_filter(contextfilter(partial(snakecase, separator="-")))
kebabcase = as_filter(contextfilter(partial(snakecase, separator="-")))


@as_filter
@contextfilter
def camelcase(name):
    return untitleize(pascalcase(name))


@as_filter
@contextfilter
def pascalcase(name, rx=re.compile("[\-_ ]")):
    return "".join(titleize(x) for x in rx.split(name))


@as_filter
@contextfilter
def titleize(name):
    if not name:
        return name
    name = str(name)
    return "{}{}".format(name[0].upper(), name[1:])


@as_filter
@contextfilter
def untitleize(name):
    if not name:
        return name
    return "{}{}".format(name[0].lower(), name[1:])
