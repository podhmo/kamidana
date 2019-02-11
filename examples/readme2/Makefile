OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00

dst:
	mkdir -p dst

00: dst
	kamidana ${OPTS} --additionals=./additionals.py --data=./data.yaml src/hello.jinja2 ${TEE} dst/00hello.output
