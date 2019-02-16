default: 00 01 02 03 04 05

OPTS ?= --logging=DEBUG
MASK ?= 2>&1 | sed "s@$(shell cd ../../; pwd)@HERE@"
TEE ?= | tee

dst:
	mkdir -p dst
clean:
	rm -rf dst

# extends
00: dst
	mkdir -p dst/00
	kamidana src/00*/*.j2 ${TEE} dst/00/output.html

# syntax error
01: dst
	# notfound
	mkdir -p dst/01
	kamidana src/01*/notfound.j2 ${MASK} ${TEE} dst/01/notfound.html || exit 0
	# {{xxx}
	kamidana src/01*/broken.j2 ${MASK} ${TEE} dst/01/broken.html || exit 0
	# unknown filter
	kamidana src/01*/unknown-filter.j2 ${MASK} ${TEE} dst/01/unknown-filter.html || exit 0
# todo: undefined

# include
02: dst
	mkdir -p dst/02
	kamidana src/02*/main.html.j2 ${MASK} ${TEE} dst/02/include.html
# todo: include 404

# runtime error
03: dst
	mkdir -p dst/03
	# using use directly
	kamidana src/03*/zero.div.html.j2 ${MASK} ${TEE} dst/03/zero.div.html || exit 0
	# main (use indirectly)
	kamidana src/03*/main.html.j2 ${MASK} ${TEE} dst/03/main.html

# filter
04: dst
	mkdir -p dst/04
	# main
	kamidana src/04*/main.html.j2 ${MASK} ${TEE} dst/04/main.html
	# missing-filter directly
	kamidana src/04*/missing-filter.html.j2 ${MASK} ${TEE} dst/04/missing-filter.html || exit 0
	# invalid-filter directly
	kamidana -a src/04*/additionals.py src/04*/invalid-filter.html.j2 ${MASK} ${TEE} dst/04/invalid-filter.html || exit 0
	# main-error (use indirectly)
	kamidana -a src/04*/additionals.py src/04*/main-error.html.j2 ${MASK} ${TEE} dst/04/main-error.html


05: dst
	mkdir -p dst/05
	kamidana src/05*/main.j2 ${MASK} ${TEE} dst/05/main.output
	# error
	kamidana src/05*/main-error.j2 ${MASK} ${TEE} dst/05/main-error.output
	# error on import
	kamidana src/05*/main-error-on-import.j2 ${MASK} ${TEE} dst/05/main-error-on-import.output
