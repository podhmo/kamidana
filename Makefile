default: readme docs

readme:
	kamidana misc/readme.rst.jinja2 --additionals kamidana.additionals.reader > README.rst

docs:
	$(MAKE) html -C docs
.PHONY: docs
