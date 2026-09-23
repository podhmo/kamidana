# kamidana

kamidana is a cli wrapper around jinja2.

features

- render a jinja2 template file from the command line
- load a template bundled in a python package (e.g. `mypkg/templates/main.j2`)
- read data in various formats (json, yaml, toml, ...)
- resolve extends/include relative to the parent template
- gentle error messages when rendering fails
- render many files in one run (`kamidana-batch`)
- register your own filters, tests and globals (`--additionals`)
- builtin additionals modules (e.g. `kamidana.additionals.naming`)

## install

```console
$ pip install kamidana
```

(python >= 3.10 is required)

## usage

```console
usage: kamidana [-h] [--loader LOADER] [-d FILE] [--data-json JSON]
                  [--logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}] [-a ADDITIONALS] [-e EXTENSION]
                  [-i {yaml,json,toml,csv,tsv,raw,env,md,markdown,spreadsheet}] [-o OUTPUT_FORMAT]
                  [--strict-undefined | --no-strict-undefined] [--debug] [--quiet] [--driver DRIVER] [--dump-context]
                  [--list-info] [--dst DST]
                  [template]

  positional arguments:
    template              template file ('./foo.j2', '../foo.j2', '/foo.j2') or a template in a python package
                          ('<package>/<path>')

  options:
    -h, --help            show this help message and exit
    --loader LOADER       default: kamidana.loader:TemplateLoader
    -d FILE, --data FILE  data file (yaml, json, toml). merged with --data-json in argv order; later wins
    --data-json JSON      literal JSON object (e.g. '{"name": "foo"}'). same merge tier as -d/--data
    --logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}
    -a ADDITIONALS, --additionals ADDITIONALS
    -e EXTENSION, --extension EXTENSION
    -i {yaml,json,toml,csv,tsv,raw,env,md,markdown,spreadsheet}, --input-format {yaml,json,toml,csv,tsv,raw,env,md,markdown,spreadsheet}
    -o OUTPUT_FORMAT, --output-format OUTPUT_FORMAT
    --strict-undefined, --no-strict-undefined
                          raise an error when an undefined variable is used (jinja2.StrictUndefined; --no-strict-
                          undefined renders it empty)
    --debug
    --quiet
    --driver DRIVER       default: kamidana.driver:Driver
    --dump-context        dumping loading data (used by jinja2 template)
    --list-info           listting information (for available extensions and additional modules)
    --dst DST

```

### template name

a template name is resolved in one of two ways.

- **physical path**: a name starting with `./`, `../` or `/` is a file path
  - `./main.j2` -> the file `main.j2` in the current directory
  - `../main.j2` -> the file `main.j2` in the parent directory
  - `/tmp/main.j2` -> the file `/tmp/main.j2`
- **python package**: otherwise, the name is a template in a python package, in `<package>/<path>` form
  - `mypkg/templates/main.j2` -> the resource `templates/main.j2` inside the installed package `mypkg`
  - `mypkg.sub/templates/main.j2` -> a dotted package name is also ok (resolved via `importlib.resources`)

the same rule applies to `-a/--additionals`, which accepts a file path (`foo/bar.py`) or a module name (`foo.bar`).

```console
$ kamidana main.j2                   # NG: interpreted as a package template
$ kamidana ./main.j2                 # OK: the file main.j2
$ kamidana mypkg/templates/main.j2   # OK: the template "templates/main.j2" in package "mypkg"
```

so a file in the current directory needs the `./` prefix.
when a template name cannot be resolved, the error message explains the rule
(e.g. `"main.j2" exists in the current directory, but "main.j2" is interpreted as a template in a python package. to load the file, pass "./main.j2"`).

in both cases, `{% extends %}` and `{% include %}` resolve relative to the parent template —
`{% extends "base.j2" %}` inside `mypkg/templates/main.j2` loads `templates/base.j2` from the same package.

in `kamidana-batch`, each command's `template` field follows the same rule.

### undefined variables

by default, referencing a variable that was not passed raises an error
(jinja2.StrictUndefined), and the gentle error message shows where it happened.

```console

$ kamidana ./examples/readme/src/12/person.j2 -d examples/readme/src/12/data.yaml
------------------------------------------------------------
  exception: jinja2.exceptions.UndefinedError
  message: 'age' is undefined
  where: examples/readme/src/12/person.j2
  ------------------------------------------------------------
  examples/readme/src/12/person.j2:
        1: name: {{ name }}
    ->  2: age: {{ age }}


```

pass `--no-strict-undefined` to render missing variables as empty instead
(jinja2's own default).

```console

$ kamidana ./examples/readme/src/12/person.j2 -d examples/readme/src/12/data.yaml --no-strict-undefined
name: foo
  age: 


```

## examples

### example (basic)

```console

$ kamidana ./examples/readme/src/00/nginx.jinja2 --data examples/readme/src/00/data.json
server {
    listen 80;
    server_name localhost;

    root /var/www/project;
    index index.htm;

    access_log /var/log/nginx/http.access.log combined;
    error_log  /var/log/nginx/http.error.log;
  }


```


examples/readme/src/00/nginx.jinja2

```
server {
    listen 80;
    server_name {{ nginx.hostname }};

    root {{ nginx.webroot }};
    index index.htm;

    access_log {{ nginx.logdir }}/http.access.log combined;
    error_log  {{ nginx.logdir }}/http.error.log;
  }

```



examples/readme/src/00/data.json

```json
{
    "nginx": {
      "hostname": "localhost",
      "webroot": "/var/www/project",
      "logdir": "/var/log/nginx"
    }
  }

```


data can also be read from stdin (don't forget `--input-format`).

```console

$ echo '{"nginx": {"logdir": "/tmp/logs/nginx"}}' | kamidana --input-format json ./examples/readme/src/00/nginx.jinja2 --data examples/readme/src/00/data.json
server {
    listen 80;
    server_name localhost;

    root /var/www/project;
    index index.htm;

    access_log /tmp/logs/nginx/http.access.log combined;
    error_log  /tmp/logs/nginx/http.error.log;
  }


```

#### literal JSON data (--data-json)

a small one-off value can be passed directly as a JSON object, without a data file.

```console

$ kamidana ./examples/readme/src/00/nginx.jinja2 --data examples/readme/src/00/data.json --data-json '{"nginx": {"logdir": "/tmp/logs/nginx"}}'
server {
    listen 80;
    server_name localhost;

    root /var/www/project;
    index index.htm;

    access_log /tmp/logs/nginx/http.access.log combined;
    error_log  /tmp/logs/nginx/http.error.log;
  }


```

`-d/--data` and `--data-json` are on the same tier: they merge in command-line order and the later one wins — whatever comes first acts as the defaults. (both are repeatable)

```console
$ kamidana ./t.j2 -d defaults.yaml --data-json '{"user_name": "world"}'   # defaults.yaml is the default, JSON overrides
$ kamidana ./t.j2 --data-json '{"user_name": "world"}' -d override.yaml   # the reverse order also works
```

`-i/--input-format` (stdin) is always merged last, so it has the highest precedence.

```
[-d | --data-json]  in argv order  ->  -i stdin   (later wins)
```

note: `--data-json` takes a JSON object (e.g. `{"x": 1}`). when two sources set the same key, the later one wins; arrays are replaced, not concatenated.

### gentle error message

when an included template is not found, the error shows where it happened:

```console

$ tree ./examples/readme/src/11
./examples/readme/src/11
  ├── header.html.j2
  └── main.html.j2

  0 directories, 2 files


```

```console

$ kamidana ./examples/readme/src/11/main.html.j2
------------------------------------------------------------
  exception: kamidana._path.XTemplatePathNotFound
  message: [Errno 2] No such file or directory: 'footer-404.html.j2'. (a template name is a file if it starts with './', '../' or '/'; otherwise it is a template in a python package ('<package>/<path>'))
  where: examples/readme/src/11/main.html.j2
  ------------------------------------------------------------
  examples/readme/src/11/main.html.j2:
        2: <main>
        3:   this is main contents
        4: </main>
    ->  5: {% include "footer-404.html.j2" %}

  Traceback:
    File "SITE-PACKAGES/jinja2/loaders.py", line N, in get_source
      rv = self.load_func(template)
    File "src/kamidana/loader.py", line 50, in load
      return self._load_from_file(filename)
    File "src/kamidana/loader.py", line 62, in _load_from_file
      raise XTemplatePathNotFound(filename, exc=exc).with_traceback(e.__traceback__)
    File "src/kamidana/loader.py", line 57, in _load_from_file
      with open(filename) as rf:


```

### example2 (--additionals)

#### builtin additional modules

```console

$ kamidana --additionals=kamidana.additionals.naming ./examples/readme/src/01/use-naming.jinja2
singular, plurals

  - days|singularize -> day
  - day|pluralize -> days

  - people|singularize -> person
  - person|pluralize -> people

  to {snake_case, kebab-case, camelCase}

  - fooBarBoo|snakecase -> foo_bar_boo
  - fooBarBoo|kebabcase -> foo-bar-boo
  - foo_bar_boo|camelcase -> fooBarBoo


  more information: see kamidana.additionals.naming module


```


examples/readme/src/01/use-naming.jinja2

```
singular, plurals

  - days|singularize -> {{"days"|singularize}}
  - day|pluralize -> {{"day"|pluralize}}

  - people|singularize -> {{"people"|singularize}}
  - person|pluralize -> {{"person"|pluralize}}

  to {snake_case, kebab-case, camelCase}

  - fooBarBoo|snakecase -> {{"fooBarBoo"|snakecase}}
  - fooBarBoo|kebabcase -> {{"fooBarBoo"|kebabcase}}
  - foo_bar_boo|camelcase -> {{"foo_bar_boo"|camelcase}}


  more information: see kamidana.additionals.naming module

```


the shortcut `kamidana -a naming` works too.

#### custom additional modules

```console

$ kamidana --additionals=examples/readme/src/01/additionals.py --data=examples/readme/src/01/data.yaml ./examples/readme/src/01/hello.jinja2

    bye, world!!


```


examples/readme/src/01/hello.jinja2

```
{% if 19 is night %}
    {{night}}, {{name|surprised}}
  {% else %}
    {{daytime}}, {{name|surprised}}
  {% endif %}
```



examples/readme/src/01/additionals.py

```python
from kamidana import (
      as_filter,
      as_globals_generator,
      as_test,
  )


  @as_filter
  def surprised(v):
      return "{}!!".format(v)


  @as_globals_generator
  def generate_globals():
      return {"daytime": "hello", "night": "bye"}


  @as_test
  def night(hour):
      return 19 <= hour or hour < 3

```



examples/readme/src/01/data.yaml

```yaml
name: world


```


### example3 (using jinja2 extensions)

```console

$ kamidana -e do -e loopcontrols ./examples/readme/src/02/use-extension.jinja2

  hello
    world
  hello

  ## counting
  - 1
  - 2
  - 4

  ## do
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


```


examples/readme/src/02/use-extension.jinja2

```
{# with with. with_ extension is used. #}
  {%- with msg = "hello"%}
  {{msg}}
  {%- with msg = "world"%}
    {{msg}}
  {%- endwith %}
  {{msg}}
  {%- endwith %}

  ## counting
  {#- with break and continue. loopcontrolls extension is used. #}

  {%- for i in range(10) %}
  {%- if i % 3 == 0 %}{% continue %} {% endif %}
  {%- if i == 5 %}{% break %} {% endif %}
  - {{i}}
  {%- endfor %}

  ## do

  {%- set xs = [] %}
  {%- for i in range(10) %}
  {%- do xs.append(i) %}
  {%- endfor %}
  {{xs}}


```


### example4 (batch execution)

`kamidana-batch` renders many files in one run. a batch file is a JSON list of commands; each command is a mapping with `template`, `dst`, `data` and `format` keys.

- `template` -- required. the same naming rule as `kamidana` (`./foo.j2` for a file, `mypkg/path` for a package template)
- `dst` -- required. the output path, relative to `--outdir`
- `data` -- optional. a data object, a data-file path, or a list of them (a list merges its entries in order)
- `format` -- optional. parse the rendered text back as data and re-dump it (e.g. `yaml`, `json`); omit it to write the raw text

examples/batch/src/01batch.json

```json
[
    {"template": "./src/00hello.j2", "data": {"name": "foo"}, "dst": "foo.hello"},
    {"template": "./src/00hello.j2", "data": [{"name": "bar"}], "dst": "bar.hello"},
    {"template": "./src/00hello.j2", "data": "me.json", "dst": "me.hello"}
  ]

```

```console

$ cd examples/batch && kamidana-batch src/01batch.json --logging=WARNING --outdir=/tmp/kamidana-batch-readme


```

the rendered files are written under `--outdir`.

```console

$ cd examples/batch && for f in /tmp/kamidana-batch-readme/*; do echo "== $f"; cat "$f"; done
== /tmp/kamidana-batch-readme/bar.hello
  hello bar
  == /tmp/kamidana-batch-readme/foo.hello
  hello foo
  == /tmp/kamidana-batch-readme/me.hello
  hello me


```

`-d/--data` passed on the command line is merged over each command's own `data`.
(see [examples/batch](./examples/batch))

## debugging

- `--dump-context` -- dump the merged data instead of rendering
- `--debug` -- re-raise errors with the full traceback (skip the gentle error)
- `--quiet` -- print only the exception line on error

### dumping the context

```console

$ kamidana --dump-context --data=examples/readme/src/10/data.yaml
{
    "name": "foo",
    "age": 20,
    "friends": [
      "bar",
      "boo"
    ],
    "template_filename": null
  }

```

multiple data files merge in order — the later one wins.

```console

$ kamidana --dump-context --data=examples/readme/src/10/data.yaml --data=examples/readme/src/10/data2.yaml
{
    "name": "foo",
    "age": 21,
    "friends": [
      "bar",
      "baz"
    ],
    "template_filename": null
  }

```

then


examples/readme/src/10/data.yaml

```yaml
name: foo
  age: 20
  friends:
    - bar
    - boo

```



examples/readme/src/10/data2.yaml

```yaml
age: 21
  friends:
    - bar
    - baz

```


## available extensions and modules

```
$ kamidana --list-info
extensions are used by `-e`, additional modules are used by `-a`.
  {
    "extensions": {
      "jinja2.ext.i18n": "This extension adds gettext support to Jinja.",
      "jinja2.ext.do": "Adds a `do` tag to Jinja that works like the print statement just",
      "jinja2.ext.loopcontrols": "Adds break and continue to the template engine.",
      "jinja2.ext.debug": "A ``{% debug %}`` tag that dumps the available variables,",
      "kamidana.extensions.NamingModuleExtension": "extension create from kamidana.additionals.naming",
      "kamidana.extensions.ReaderModuleExtension": "extension create from kamidana.additionals.reader",
      "kamidana.extensions.CookiecutterAdditionalModulesExtension": "activate additional modules, see context['cookiecutter']['_additional_modules'], created from your cookiecutter.json"
    },
    "additional_modules": {
      "kamidana.additionals.reader": "Reading from other resources (e.g. read_from_file, read_from_command)",
      "kamidana.additionals.env": "accessing environemt variable, via env()",
      "kamidana.additionals.naming": "Naming helpers (e.g. snakecase, kebabcase, ... pluralize, singularize)"
    }
  }

```

## using with other packages

- kamidana's additionals modules can be used from [cookiecutter](https://pypi.org/project/cookiecutter/) (see [examples/extensions/src/02with-cookiecutter](https://github.com/podhmo/kamidana/blob/master/examples/extensions/src/02with-cookiecutter))
