default:
	$(MAKE) 00
	$(MAKE) 01
	diff -ur 00out 01out

# onefile
00:
	echo '{"name": "foo"}' | kamidana -i json hello.j2 --dst 00out/foo.hello
	echo '{"name": "bar"}' | kamidana -i json hello.j2 --dst 00out/bar.hello
	kamidana hello.j2 --data me.json --dst 00out/me.hello

# batch
01:
	kamidana-batch 01batch.json --outdir=01out

# batch
02:
	kamidana-batch 02batch.json --outdir=02out

clean:
	rm -rf 00out 01out
