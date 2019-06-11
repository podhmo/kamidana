import logging
from jinja2.ext import Extension
from jinja2.environment import Environment
from jinja2.utils import import_string
from dictknife import deepmerge
from .. import collect_marked_items

logger = logging.Logger(__name__)


def _build_additionals(modules) -> dict:
    additionals = {}
    for name in modules:
        logger.info("activate additional module %s", name)
        m = import_string(name)  # xxx: use magicalimport.import_module()?
        additionals = deepmerge(additionals, collect_marked_items(m))
    return additionals


def create_apply_additonal_modules_extension_class(name: str, *, doc, get_modules):
    def __init__(self, environment: Environment) -> None:
        super(cls, self).__init__(environment)

        modules = get_modules(environment)
        additionals = _build_additionals(modules)
        for name, defs in additionals.items():
            getattr(environment, name).update(defs)

    attrs = {"__doc__": doc, "__init__": __init__}
    cls = type(name, (Extension,), attrs)
    return cls


NamingModuleExtension = create_apply_additonal_modules_extension_class(
    "NamingModuleExtension",
    get_modules=lambda env: ["kamidana.additionals.naming"],
    doc="extension create from kamidana.additionals.naming",
)
ReaderModuleExtension = create_apply_additonal_modules_extension_class(
    "ReaderModuleExtension",
    get_modules=lambda env: ["kamidana.additionals.reader"],
    doc="extension create from kamidana.additionals.reader",
)

## for cookiecutter
def _extract_module_from_cookiecutter_cotext(env, *, exception_cls=ImportError):
    import inspect

    # black magic (collect context arguments, from stackframes)
    _context = None
    f = inspect.currentframe()
    while f.f_back:
        if "context" in f.f_locals:
            _context = f.f_locals["context"]
            break
        f = f.f_back
    if _context is None:
        raise exception_cls("cookiecutter's context is not found, something wrong?")
    if "cookiecutter" not in _context:
        raise exception_cls("'cookiecutter' is not found in context, something wrong??")

    if "_additional_modules" not in _context["cookiecutter"]:
        raise exception_cls("we needs '_additional_modules' in your cookiecutter.json")
    return _context["cookiecutter"]["_additional_modules"]


CookiecutterAdditionalModulesExtension = create_apply_additonal_modules_extension_class(
    "CookiecutterAdditionalModulesExtension",
    get_modules=_extract_module_from_cookiecutter_cotext,
    doc="activate additional modules, see context['cookiecutter']['_additional_modules'], created from your cookiecutter.json",
)
