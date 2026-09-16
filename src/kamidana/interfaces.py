import typing as t

# Structural contracts for --loader / --driver plugins (resolved via
# import_symbol at runtime, so duck typing is the real contract).


class ITemplateLoader(t.Protocol):
    extensions: t.List[str]
    data: t.Dict[str, t.Any]
    additionals: t.Dict[str, t.Any]

    def load(
        self, filename: str
    ) -> t.Tuple[str, str, t.Optional[t.Callable[[], bool]]]:
        ...


class IDriver(t.Protocol):
    def load(self, template_file: str) -> t.Any:
        ...

    def dump(self, d: t.Any, dst: t.Optional[str]) -> t.Any:
        ...

    def run(self, src: t.Optional[str], dst: t.Optional[str]) -> t.Any:
        ...
