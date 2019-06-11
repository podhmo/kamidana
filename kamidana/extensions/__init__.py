from jinja2.ext import Extension
from jinja2.environment import Environment
from jinja2.utils import import_string
from kamidana import collect_marked_items
from dictknife import deepmerge


def _build_additionals(modules) -> dict:
    additionals = {}
    for name in modules:
        m = import_string(name)  # xxx: use magicalimport.import_module()?
        additionals = deepmerge(additionals, collect_marked_items(m))
    return additionals


def create_apply_additonal_modules_extension_class(name: str, *, modules: list):
    doc = "extension create from {}".format(", ".join(modules))

    def __init__(self, environment: Environment) -> None:
        super(cls, self).__init__(environment)
        additionals = _build_additionals(modules)
        for name, defs in additionals.items():
            getattr(environment, name).update(defs)

    attrs = {"__doc__": doc, "__init__": __init__}
    cls = type(name, (Extension,), attrs)
    return cls


NamingHelperExtension = create_apply_additonal_modules_extension_class(
    "NamingHelperExtension", modules=["kamidana.additionals.naming"]
)
ReaderHelperExtension = create_apply_additonal_modules_extension_class(
    "ReaderHelperExtension", modules=["kamidana.additionals.reader"]
)
