from pydantic import BaseModel
from kamidana.driver import Driver, _render_with_newline


class Params(BaseModel):
    name: str
    port: int
    greeting: str = "hello"


class ValidatingDriver(Driver):
    # run() is dump(transform(load(src))), so validating at the entrance of
    # transform() means nothing is rendered when params are invalid:
    # pydantic's ValidationError propagates as-is and the command stops.
    def transform(self, t):
        params = Params.model_validate(self.loader.data)
        return _render_with_newline(t, params.model_dump())
