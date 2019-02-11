OPTS ?= --logging=DEBUG
default: 00 01 02
	diff -ur dst/00 dst/01

dst:
	# xxx:
	mkdir -p dst/00 dst/01 dst/02

# onefile
00: dst
	echo '{"name": "foo"}' | kamidana ${OPTS} -i json src/00hello.j2 --dst dst/00/foo.hello
	echo '{"name": "bar"}' | kamidana ${OPTS} -i json src/00hello.j2 --dst dst/00/bar.hello
	kamidana ${OPTS} src/00hello.j2 --data me.json --dst dst/00/me.hello

# batch
01: dst
	kamidana-batch ${OPTS} src/01batch.json --outdir=dst/01

# batch
02: dst
	kamidana-batch ${OPTS} src/02batch.json --outdir=dst/02

clean:
	rm -rf dst/00 dst/01
