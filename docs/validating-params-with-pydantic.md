# validating params with pydantic

`--driver` is resolved in `kamidana/commands/onefile.py` via
`import_symbol(args.driver, ns="kamidana.driver", cwd=True)`. Because of
`cwd=True`, a local `.py` file can be passed as `<path>:<ClassName>`, so a
custom Driver can live next to your templates without being installed.

This example requires pydantic v2. pydantic is not a dependency of
kamidana, so install it yourself (`pip install pydantic`).

Put the following three files in one directory and run the commands there.

```jinja
{# template.j2 #}
{{ greeting }}, {{ name }}!
listening on port {{ port + 1 }}
```

Render valid data. `port` is coerced to `int` and `greeting` falls back to
its default:

```yaml
# data.yaml
name: foo
port: "8080"
```

```console
$ kamidana --driver=./validating_driver.py:ValidatingDriver -d data.yaml ./template.j2
hello, foo!
listening on port 8081
```

With data that lacks the required `name` and has a `port` of the wrong
type, pydantic's `ValidationError` is raised and nothing is rendered:

```yaml
# data.yaml
port: not-a-number
```

```console
$ kamidana --driver=./validating_driver.py:ValidatingDriver -d data.yaml ./template.j2
```

```text
Traceback (most recent call last):
  File ".local/bin/kamidana", line 8, in <module>
  File "kamidana/commands/onefile.py", line 64, in main
    driver.run(args.template, args.dst)
  File "kamidana/driver.py", line 72, in run
    return self.dump(self.transform(self.load(src)), dst)
  File "./validating_driver.py", line 17, in transform
    params = Params.model_validate(self.loader.data)
  File "site-packages/pydantic/main.py", line 732, in model_validate
    return cls.__pydantic_validator__.validate_python(
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Params
name
  Field required [type=missing, input_value={'port': 'not-a-number'}, input_type=CommentedMap]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
port
  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not-a-number', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/int_parsing
```

Since `run()` is `dump(transform(load(src)))`, validating at the entrance
of `transform` guarantees the template is never rendered without the
required params. Passing `model_dump()` to the template also makes
pydantic's default values (e.g. `greeting`) and coerced values
(e.g. `port` as `int`) available in the template.

```python
# validating_driver.py
from pydantic import BaseModel
from kamidana.driver import Driver


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
        r = t.render(**params.model_dump())
        if r.endswith("\n"):
            return r
        return r + "\n"
```
