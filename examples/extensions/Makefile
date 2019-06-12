OPTS ?= --logging=DEBUG
TEE ?= | tee

default: 00 01 02

dst:
	mkdir -p dst

# use extension applyging additional modules
00: dst
	python src/00*.py ${TEE} dst/00.output
01: dst
	kamidana ${OPTS} src/01use-naming.j2 -e "kamidana.extensions:NamingModuleExtension" ${TEE} dst/01.output

# :warning: external dependency: cookiecutter
02: outdir := dst/02with-cookiecutter
02: dst
	rm -rf ${outdir}
	cookiecutter src/02with-cookiecutter/with_additional_modules --no-input -o ${outdir}
