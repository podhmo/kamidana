from __future__ import annotations

import logging
from functools import partial
from jinja2.ext import Extension
from jinja2.environment import Environment
from jinja2 import utils as j2utils
from dictknife.deepmerge import deepmerge
from typing import TYPE_CHECKING
from .. import collect_marked_items
from .._import import import_module

if TYPE_CHECKING:
    import typing as t
    from types import ModuleType

logger = logging.getLogger(__name__)


def _build_additionals(
    modules: t.Iterable[str], *, import_string: t.Callable[[str], t.Any]
) -> t.Dict[str, t.Dict[str, t.Any]]:
    additionals: t.Dict[str, t.Dict[str, t.Any]] = {}
    for name in modules:
        logger.info("activate additional module %s", name)
        m = import_string(name)  # xxx: use magicalimport.import_module()?
        additionals = deepmerge(additionals, collect_marked_items(m))
    return additionals


def create_apply_additonal_modules_extension_class(
    name: str,
    *,
    doc: t.Optional[str],
    get_modules: t.Callable[
        [Environment], t.Tuple[t.List[str], t.Callable[[str], t.Any]]
    ],
) -> t.Type[Extension]:
    def __init__(self: Extension, environment: Environment) -> None:
        Extension.__init__(self, environment)

        modules, import_string = get_modules(environment)
        additionals = _build_additionals(modules, import_string=import_string)
        for name, defs in additionals.items():
            getattr(environment, name).update(defs)

    attrs: t.Dict[str, t.Any] = {"__doc__": doc, "__init__": __init__}
    cls = type(name, (Extension,), attrs)
    return cls


NamingModuleExtension = create_apply_additonal_modules_extension_class(
    "NamingModuleExtension",
    get_modules=lambda env: (["kamidana.additionals.naming"], j2utils.import_string),
    doc="extension create from kamidana.additionals.naming",
)
ReaderModuleExtension = create_apply_additonal_modules_extension_class(
    "ReaderModuleExtension",
    get_modules=lambda env: (["kamidana.additionals.reader"], j2utils.import_string),
    doc="extension create from kamidana.additionals.reader",
)


# for cookiecutter
def _extract_module_from_cookiecutter_cotext(
    env: Environment, *, exception_cls: t.Type[Exception] = ImportError
) -> t.Tuple[t.Any, t.Callable[..., ModuleType]]:
    import inspect

    # :WARGNING:
    # todo: drop inspect.currentframe()

    # black magic (collect context argument, from stackframes)
    _context = None
    f = inspect.currentframe()
    while f is not None and f.f_back is not None:
        if "context" in f.f_locals:
            _context = f.f_locals["context"]
            break
        f = f.f_back
    if _context is None:
        raise exception_cls("cookiecutter's context is not found, something wrong?")
    if "cookiecutter" not in _context:
        raise exception_cls("'cookiecutter' is not found in context, something wrong??")

    # black magic (collect the value of repo_dir variable on cookiecutter.main:cookiecutter())
    _repo_dir = None
    while f is not None and f.f_back is not None:
        if "repo_dir" in f.f_locals:
            _repo_dir = f.f_locals["repo_dir"]
            break
        f = f.f_back

    if "_additional_modules" not in _context["cookiecutter"]:
        raise exception_cls("we needs '_additional_modules' in your cookiecutter.json")
    return (
        _context["cookiecutter"]["_additional_modules"],
        partial(import_module, here=_repo_dir, cwd=True),
    )


CookiecutterAdditionalModulesExtension = create_apply_additonal_modules_extension_class(
    "CookiecutterAdditionalModulesExtension",
    get_modules=_extract_module_from_cookiecutter_cotext,
    doc="activate additional modules, see context['cookiecutter']['_additional_modules'], created from your cookiecutter.json",
)
