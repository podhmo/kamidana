default: readme docs

readme:
	kamidana misc/readme.rst.jinja2 --additionals kamidana.additionals.reader > README.rst

docs:
	$(MAKE) html -C docs
.PHONY: docs

# integration tests (regression tests)
WHERE ?= .
run:
	$(MAKE) --silent _find-candidates | xargs -n 1 make -C || (echo "**********NG**********" && exit 1)
ci:
	$(MAKE) --silent _find-candidates | xargs -n 1 echo "OPTS=--logging=WARNING" make --silent -C | bash -x -e || (echo "**********NG**********" && exit 1)
	test -z `git diff` || (echo  "*********DIFF*********" && git diff && exit 2)
_find-candidates:
	@find ${WHERE} -mindepth 2 -name Makefile | grep -v optional/sheet | grep -v docs | xargs -n 1 -I{} dirname {}
