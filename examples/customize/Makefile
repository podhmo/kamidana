default: 00
OPTS ?= --logging=DEBUG
TEE ?= | tee

dst:
	mkdir -p dst

# custom loader
00: dst
	mkdir -p dst/00
	kamidana ${OPTS} --data=src/00/data.yaml --loader=src/00/loader.py:WithHeaderLoader src/00/use_customloader.py.j2 ${TEE} dst/00/use_customloader.py
