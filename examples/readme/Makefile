OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00

dst:
	mkdir -p dst

00: dst
	kamidana --data data.json src/nginx.jinja2 ${TEE} dst/00nginx.conf
