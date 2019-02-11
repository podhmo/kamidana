OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00

dst:
	mkdir -p dst



00: dst
	kamidana ${OPTS} -e with_ -e do -e loopcontrols hello.jinja2 ${TEE} dst/00.output
