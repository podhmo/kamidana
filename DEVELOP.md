# development

## setup

```console
$ pip install -e .[testing]
```

## tests, lint, typecheck

```console
$ pytest          # unit tests
$ make ci         # examples regression; also asserts a clean git diff
$ flake8          # lint
$ make typecheck  # mypy --strict
```

## README.md

README.md is generated from `misc/readme.md.jinja2` (kamidana renders itself).
edit the template, then regenerate:

```console
$ make readme
```

## release

the version lives in `VERSION`, and the changelog is `CHANGES.txt` — it is also
shipped as part of the package readme on PyPI, so keep each released version's
section accurate.

to cut a release:

1. update `CHANGES.txt` (write the entry for the version being released)
2. bump `VERSION`
3. commit, tag, build, upload

```console
$ git tag "$(cat VERSION)"   # e.g. 0.11.0
$ make build                 # python -m build -> dist/
$ make upload                # twine check + twine upload
```
