OPTS ?= --logging=DEBUG
default: 00 01 02
	diff -ur dst/00 dst/01

dst:
	mkdir -p dst

# onefile
00:
	echo '{"name": "foo"}' | kamidana ${OPTS} -i json src/00hello.j2 --dst dst/00/foo.hello
	echo '{"name": "bar"}' | kamidana ${OPTS} -i json src/00hello.j2 --dst dst/00/bar.hello
	kamidana ${OPTS} src/00hello.j2 --data me.json --dst dst/00/me.hello

# batch
01:
	kamidana-batch ${OPTS} src/01batch.json --outdir=dst/01

# batch
02:
	kamidana-batch ${OPTS} src/02batch.json --outdir=dst/02

clean:
	rm -rf dst/00 dst/01
