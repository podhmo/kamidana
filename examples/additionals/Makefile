OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00 01 02 03 04

dst:
	mkdir -p dst

# naming
00: dst
	kamidana ${OPTS} -a kamidana.additionals.naming src/00*.jinja2 ${TEE} dst/00.output
01: dst
	kamidana ${OPTS} -a kamidana.additionals.naming src/01*.jinja2 ${TEE} dst/01.output

# reader
02: dst
	kamidana ${OPTS} -a kamidana.additionals.reader src/02*.jinja2 ${TEE} dst/02.output

# import with shortname
03: dst 02
	kamidana ${OPTS} -a reader src/02*.jinja2 ${TEE} dst/03.output
	test -z `diff -u dst/02.output dst/03.output`

# relative import (passing physical path)
04: dst
	kamidana ${OPTS} -a scream.py src/04*.jinja2 ${TEE} dst/04.output

