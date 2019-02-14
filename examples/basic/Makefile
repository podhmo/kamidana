default: 00 01
MASK ?= 2>&1 | sed "s@$(shell cd ../../; pwd)@HERE@"
TEE ?= | tee

dst:
	mkdir -p dst

00: dst
	mkdir -p dst/00
	kamidana src/00*/*.j2 ${TEE} dst/00/output.html

01: dst
	# notfound
	mkdir -p dst/01
	kamidana src/01*/notfound.j2 ${MASK} ${TEE} dst/01/notfound.html || exit 0
	# {{xxx}
	kamidana src/01*/broken.j2 ${MASK} ${TEE} dst/01/broken.html || exit 0
	# unknown filter
	kamidana src/01*/unknown-filter.j2 ${MASK} ${TEE} dst/01/unknown-filter.html || exit 0
