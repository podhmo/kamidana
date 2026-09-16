OPTS ?= --logging=INFO
TEE ?= | tee

default: 00

dst:
	mkdir -p dst

# template in a python package (e.g. <package>/<path>)
00: dst
	PYTHONPATH=./src kamidana ${OPTS} demopkg/templates/hello.j2 ${TEE} dst/00.output
