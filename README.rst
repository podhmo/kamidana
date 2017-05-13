kamidana
========================================

.. image:: https://travis-ci.org/podhmo/kamidana.svg?branch=master
    :target: https://travis-ci.org/podhmo/kamidana

example
----------------------------------------

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


.. code-block:: bash

  $ kamidana examples/readme/nginx.jinja2 --data examples/readme/data.json
  server {
    listen 80;
    server_name localhost;
  
    root /var/www/project;
    index index.htm;
  
    access_log /var/log/nginx/http.access.log combined;
    error_log  /var/log/nginx/http.error.log;
  }

