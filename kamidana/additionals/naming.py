import re
import inflection
from kamidana import as_filter

pluralize = as_filter(inflection.pluralize)
singularize = as_filter(inflection.singularize)


@as_filter
def snakecase(
    name, rx0=re.compile('(.)([A-Z][a-z]+)'), rx1=re.compile('([a-z0-9])([A-Z])'), separator="_"
):
    pattern = r'\1{}\2'.format(separator)
    return rx1.sub(pattern, rx0.sub(pattern, name)).lower()


@as_filter
def kebabcase(name):
    return snakecase(name, separator="-")


@as_filter
def lispcase(name):  # alias
    return snakecase(name, separator="-")


@as_filter
def camelcase(name):
    return untitleize(pascalcase(name))


@as_filter
def pascalcase(name, rx=re.compile("[\-_ ]")):
    return "".join(titleize(x) for x in rx.split(name))


@as_filter
def titleize(name):
    if not name:
        return name
    name = str(name)
    return "{}{}".format(name[0].upper(), name[1:])


@as_filter
def untitleize(name):
    if not name:
        return name
    return "{}{}".format(name[0].lower(), name[1:])
