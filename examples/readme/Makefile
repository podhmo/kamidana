OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00 01 02

dst:
	mkdir -p dst

00: dst
	mkdir -p dst/00
	kamidana --data src/00/data.json src/00/nginx.jinja2 ${TEE} dst/00/nginx.conf

01: dst
	mkdir -p dst/01
	kamidana ${OPTS} --additionals=src/01/additionals.py --data=src/01/data.yaml src/01/hello.jinja2 ${TEE} dst/01/hello.output

02: dst
	mkdir -p dst/02
	kamidana ${OPTS} -e with_ -e do -e loopcontrols src/02/use-extension.jinja2 ${TEE} dst/02/use-extension.output
