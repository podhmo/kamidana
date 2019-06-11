OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00 01

dst:
	mkdir -p dst

# use extension applyging additional modules
00: dst
	python src/00*.py ${TEE} dst/00.output
01: dst
	kamidana ${OPTS} src/01use-naming.j2 -e "kamidana.extensions:NamingExtension" ${TEE} dst/01.output
