kamidana
========================================

.. image:: https://travis-ci.org/podhmo/kamidana.svg?branch=master
    :target: https://travis-ci.org/podhmo/kamidana

kamidana is yet another jinja2's cli wrapper.

features

- using jinja2 file as template file (basic feature)
- various input formats support (json, yaml, toml, ...)
- the way of lookup template is changed, relative to parent template path
- gentle error message
- batch execution for speed-up (via `kamidana-batch`)
- rendering with individual filters (via `--additionals` option)
- (useful additionals modules (e.g. `kamidana.additionals.naming` ...)

usage
----------------------------------------

.. code-block:: console

  usage: kamidana [-h] [--driver DRIVER] [--loader LOADER] [-d DATA]
                  [--logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}] [-a ADDITIONALS] [-e EXTENSION]
                  [-i {yaml,json,toml,csv,tsv,raw,env,md,markdown,spreadsheet}] [-o OUTPUT_FORMAT] [--dump-context]
                  [--list-info] [--debug] [--quiet] [--dst DST]
                  [template]

  positional arguments:
    template

  optional arguments:
    -h, --help            show this help message and exit
    --driver DRIVER       default: kamidana.driver:Driver
    --loader LOADER       default: kamidana.loader:TemplateLoader
    -d DATA, --data DATA  support yaml, json, toml
    --logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}
    -a ADDITIONALS, --additionals ADDITIONALS
    -e EXTENSION, --extension EXTENSION
    -i {yaml,json,toml,csv,tsv,raw,env,md,markdown,spreadsheet}, --input-format {yaml,json,toml,csv,tsv,raw,env,md,markdown,spreadsheet}
    -o OUTPUT_FORMAT, --output-format OUTPUT_FORMAT
    --dump-context        dumping loading data (used by jinja2 template)
    --list-info           listting information (for available extensions and additional modules)
    --debug
    --quiet
    --dst DST


examples
----------------------------------------

example (basic)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console


  $ kamidana examples/readme/src/00/nginx.jinja2 --data examples/readme/src/00/data.json
  server {
    listen 80;
    server_name localhost;

    root /var/www/project;
    index index.htm;

    access_log /var/log/nginx/http.access.log combined;
    error_log  /var/log/nginx/http.error.log;
  }




examples/readme/src/00/nginx.jinja2

.. code-block::

  server {
    listen 80;
    server_name {{ nginx.hostname }};

    root {{ nginx.webroot }};
    index index.htm;

    access_log {{ nginx.logdir }}/http.access.log combined;
    error_log  {{ nginx.logdir }}/http.error.log;
  }




examples/readme/src/00/data.json

.. code-block:: json

  {
    "nginx": {
      "hostname": "localhost",
      "webroot": "/var/www/project",
      "logdir": "/var/log/nginx"
    }
  }



More over, passing data with stdin. (please doen't forget to add `--input-format` option)

.. code-block:: console


  $ echo '{"nginx": {"logdir": "/tmp/logs/nginx"}}' | kamidana --input-format json examples/readme/src/00/nginx.jinja2 --data examples/readme/src/00/data.json
  server {
    listen 80;
    server_name localhost;

    root /var/www/project;
    index index.htm;

    access_log /tmp/logs/nginx/http.access.log combined;
    error_log  /tmp/logs/nginx/http.error.log;
  }



gentle error message
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

if using include, but the included template is not found.

.. code-block:: console


  $ tree examples/readme/src/11
  examples/readme/src/11
  ├── header.html.j2
  └── main.html.j2

  0 directories, 2 files



.. code-block:: console


  $ kamidana examples/readme/src/11/main.html.j2
  ------------------------------------------------------------
  exception: kamidana._path.XTemplatePathNotFound
  message: [Errno 2] No such file or directory: 'footer-404.html.j2'
  where: examples/readme/src/11/main.html.j2
  ------------------------------------------------------------
  examples/readme/src/11/main.html.j2:
        2: <main>
        3:   this is main contents
        4: </main>
    ->  5: {% include "footer-404.html.j2" %}

  Traceback:
    File "SITE-PACKAGES/jinja2/loaders.py", line 314, in get_source
      rv = self.load_func(template)
    File "HERE/my/kamidana/kamidana/loader.py", line 27, in load
      raise XTemplatePathNotFound(filename, exc=e).with_traceback(e.__traceback__)
    File "HERE/my/kamidana/kamidana/loader.py", line 23, in load
      with open(filename) as rf:



example2 (--additionals)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

builtin addtional modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console


  $ kamidana --additionals=kamidana.additionals.naming examples/readme/src/01/use-naming.jinja2
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





examples/readme/src/01/use-naming.jinja2

.. code-block::

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



or `kamidana -a naming` is also OK (shortcut).

individual additional modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console


  $ kamidana --additionals=examples/readme/src/01/additionals.py --data=examples/readme/src/01/data.yaml examples/readme/src/01/hello.jinja2
  
    bye, world!!




examples/readme/src/01/hello.jinja2

.. code-block::

  {% if 19 is night %}
    {{night}}, {{name|surprised}}
  {% else %}
    {{daytime}}, {{name|surprised}}
  {% endif %}




examples/readme/src/01/additionals.py

.. code-block:: python

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




examples/readme/src/01/data.yaml

.. code-block:: yaml

  name: world




example3 (using jinja2 extensions)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console


  $ kamidana -e with_ -e do -e loopcontrols examples/readme/src/02/use-extension.jinja2
  
  hello
    world
  hello

  ## counting
  - 1
  - 2
  - 4

  ## do
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]




examples/readme/src/02/use-extension.jinja2

.. code-block::

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




example4 (batch execution)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TODO. `see this <./examples/batch>`_


debugging
----------------------------------------

- `--dump-context`
- `--debug`

dump context
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console


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


and be able to merge two files.

.. code-block:: console


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


then


examples/readme/src/10/data.yaml

.. code-block:: yaml

  name: foo
  age: 20
  friends:
    - bar
    - boo




examples/readme/src/10/data2.yaml

.. code-block:: yaml

  age: 21
  friends:
    - bar
    - baz



available info (extensions and additional modules)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block::

  [1mextensions are used by `-e`, additional modules are used by `-a`.[0m
  {
    "extensions": {
      "jinja2.ext.i18n": "This extension adds gettext support to Jinja2.",
      "jinja2.ext.do": "Adds a `do` tag to Jinja2 that works like the print statement just",
      "jinja2.ext.loopcontrols": "Adds break and continue to the template engine.",
      "jinja2.ext.with_": "Extensions can be used to add extra functionality to the Jinja template",
      "jinja2.ext.autoescape": "Extensions can be used to add extra functionality to the Jinja template",
      "kamidana.extensions.NamingModuleExtension": "extension create from kamidana.additionals.naming",
      "kamidana.extensions.ReaderModuleExtension": "extension create from kamidana.additionals.reader",
      "kamidana.extensions.CookiecutterAdditionalModulesExtension": "activate additional modules, see context['cookiecutter']['_additional_modules'], created from your cookiecutter.json"
    },
    "additional_modules": {
      "kamidana.additionals.reader": "Reading from other resources (e.g. read_from_file, read_from_command)",
      "kamidana.additionals.naming": "Naming helpers (e.g. snakecase, kebabcase, ... pluralize, singularize)",
      "kamidana.additionals.env": "accessing environemt variable, via env()"
    }
  }
