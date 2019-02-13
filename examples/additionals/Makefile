OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00 01

dst:
	mkdir -p dst

# naming
00: dst
	kamidana ${OPTS} -a kamidana.additionals.naming src/00*.jinja2 ${TEE} dst/00.output
01: dst
	kamidana ${OPTS} -a kamidana.additionals.naming src/01*.jinja2 ${TEE} dst/01.output
