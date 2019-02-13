OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00

dst:
	mkdir -p dst

00: dst
	mkdir -p dst/00
	kamidana --data src/00/data.json src/00/nginx.jinja2 ${TEE} dst/00/nginx.conf
