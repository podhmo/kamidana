kamidana
========================================

.. image:: https://travis-ci.org/podhmo/kamidana.svg?branch=master
    :target: https://travis-ci.org/podhmo/kamidana

example
----------------------------------------


.. code-block:: console

  $ kamidana ../examples/readme/nginx.jinja2 --data ../examples/readme/data.json
  server {
    listen 80;
    server_name localhost;

    root /var/www/project;
    index index.htm;

    access_log /var/log/nginx/http.access.log combined;
    error_log  /var/log/nginx/http.error.log;
  }

nginx.jinja2

.. code-block:: jinja2

  server {
    listen 80;
    server_name {{ nginx.hostname }};

    root {{ nginx.webroot }};
    index index.htm;

    access_log {{ nginx.logdir }}/http.access.log combined;
    error_log  {{ nginx.logdir }}/http.error.log;
  }


data.json

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

  $ kamidana --additionals=../examples/readme2/additionals.py --data=../examples/readme2/data.yaml ../examples/readme2/hello.jinja2
    bye, world!!


hello.jinja2

.. code-block:: jinja2

  {% if 19 is night %}
    {{night}}, {{name|surprised}}
  {% else %}
    {{daytime}}, {{name|surprised}}
  {% endif %}

additionals.py

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


data.yaml

.. code-block:: yaml

  name: world


