OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00

dst:
	mkdir -p dst

00: dst
	kamidana ${OPTS} -a kamidana.additionals.naming hello.jinja2 ${TEE} dst/hello.output
