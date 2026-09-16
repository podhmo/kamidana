from pydantic import BaseModel
from kamidana.driver import Driver, _render_with_newline


class Params(BaseModel):
    name: str
    port: int
    greeting: str = "hello"


class ValidatingDriver(Driver):
    # Validate before rendering so invalid input never reaches the template.
    def transform(self, t):
        params = Params.model_validate(self.loader.data)
        return _render_with_newline(t, params.model_dump())
