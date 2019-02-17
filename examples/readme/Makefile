OPTS ?= --logging=INFO
TEE ?= | tee
MASK ?= 2>&1 | sed 's@$(shell cd ../../; pwd)@HERE@g; s@".*/site-packages@"SITE-PACKAGES@g'

default: 00 01 02 10 11

dst:
	mkdir -p dst

00: dst
	mkdir -p dst/00
	kamidana --data src/00/data.json src/00/nginx.jinja2 ${TEE} dst/00/nginx.conf
	echo '{"nginx": {"logdir": "/tmp/logs/nginx"}}' kamidana --data src/00/data.json src/00/nginx.jinja2 ${TEE} dst/00/nginx-with-stdin.conf

01: dst
	mkdir -p dst/01
	kamidana ${OPTS} --additionals=src/01/additionals.py --data=src/01/data.yaml src/01/hello.jinja2 ${TEE} dst/01/hello.output
	kamidana ${OPTS} --additionals=kamidana.additionals.naming src/01/use-naming.jinja2 ${TEE} dst/01/use-naming.output

02: dst
	mkdir -p dst/02
	kamidana ${OPTS} -e with_ -e do -e loopcontrols src/02/use-extension.jinja2 ${TEE} dst/02/use-extension.output

# --dump-context
10: dst
	mkdir -p dst/10
	kamidana ${OPTS} --data src/10/data.yaml --data src/10/data2.yaml --dump-context ${TEE} dst/10/dump-context.output

# gentle error message
11: dst
	mkdir -p dst/11
	kamidana ${OPTS} src/11/main.html.j2 ${MASK} ${TEE} dst/11/error-include-404.html
