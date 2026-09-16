from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import jinja2

# Structural contracts for --loader / --driver plugins (resolved via
# import_symbol at runtime, so duck typing is the real contract).


class ITemplateLoader(t.Protocol):
    extensions: t.List[str]

    @property
    def data(self) -> t.Dict[str, t.Any]:
        ...

    @property
    def additionals(self) -> t.Dict[str, t.Any]:
        ...

    def load(
        self, filename: str
    ) -> t.Tuple[str, str, t.Optional[t.Callable[[], bool]]]:
        ...


class IDriver(t.Protocol):
    undefined: t.Type[jinja2.Undefined]

    def load(self, template_file: t.Optional[str]) -> t.Any:
        ...

    def dump(self, d: t.Any, dst: t.Optional[str]) -> t.Any:
        ...

    def run(self, src: t.Optional[str], dst: t.Optional[str]) -> t.Any:
        ...
