default: 00 01 02 03 04

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

# runtime error2 (filter)
04: dst
	mkdir -p dst/04
	# missing directly
	kamidana src/04*/missing.html.j2 ${MASK} ${TEE} dst/04/missing.html || exit 0
	# error directly
	kamidana -a src/04*/additionals.py src/04*/invalid-filter.html.j2 ${MASK} ${TEE} dst/04/invalid-filter.html || exit 0
	# main (use indirectly)
	kamidana -a src/04*/additionals.py src/04*/main.html.j2 ${MASK} ${TEE} dst/04/main.html

# todo: import
