kamidana
========================================

.. image:: https://travis-ci.org/podhmo/kamidana.svg?branch=master
    :target: https://travis-ci.org/podhmo/kamidana

kamidana is yet another jinja2's cli wrapper.

features

- using jinja2 file as template file (basic feature)
- various input formats support (json, yaml, toml, ...)
- batch execution for speed-up (via `kamidana-batch`)
- rendering with individual filters (via `--additionals` option)
- (useful additionals modules (e.g. `kamidana.additionals.naming` ...)

usage
----------------------------------------

.. code-block:: console

  usage: kamidana [-h] [--driver DRIVER] [--loader LOADER] [-d DATA]
                  [--logging {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}]
                  [-a ADDITIONALS] [-e EXTENSION]
                  [-i {yaml,json,toml,csv,tsv,raw,env,md,markdown,spreadsheet}]
                  [-o OUTPUT_FORMAT] [--dump-context] [--debug] [--dst DST]
                  template

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
    --dump-context
    --debug
    --dst DST


examples
----------------------------------------

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

.. code-block:: jinja2

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



example2 (--additionals)
----------------------------------------

.. code-block:: console

  $ kamidana --additionals=examples/readme/src/01/additionals.py --data=examples/readme/src/01/data.yaml examples/readme/src/01/hello.jinja2
    bye, world!!



examples/readme/src/01/hello.jinja2

.. code-block:: jinja2

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


