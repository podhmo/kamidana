default: readme docs

readme:
	kamidana misc/readme.rst.jinja2 --additionals misc/additionals.py > README.rst

docs:
	$(MAKE) html -C docs
.PHONY: docs
