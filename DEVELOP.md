# development

## setup

```console
$ pip install -e .[testing]
$ pip install flake8 cookiecutter build twine   # lint, examples regression, release
```

or, from a fresh clone with [uv](https://docs.astral.sh/uv/):

```console
$ uv venv .venv --python 3.10
$ uv pip install --python .venv -e '.[testing]' flake8 cookiecutter build twine
$ export PATH=$PWD/.venv/bin:$PATH
```

## tests, lint, typecheck

```console
$ pytest          # unit tests
$ make ci         # examples regression; also asserts a clean git diff
$ flake8 . --exclude .venv --select=E9,F63,F7,F82   # lint (the errors that fail CI)
$ make typecheck  # mypy --strict
```

the expected outputs are generated on CI (ubuntu, bash). on other environments,
`make ci` may report environment-dependent diffs. e.g. on macOS with zsh,
`examples/additionals/dst/05.output` differs by `$SHELL`; run it as
`SHELL=/bin/bash make ci`.

## README.md

README.md is generated from `misc/readme.md.jinja2` (kamidana renders itself).
edit the template, then regenerate:

```console
$ make readme
```

the output depends on the python version (argparse help), the `tree` version,
and the file listing order. review the diff and keep only the intended changes.

## release

the version lives in `VERSION`, and the changelog is `CHANGES.txt` — it is also
shipped as part of the package readme on PyPI, so keep each released version's
section accurate.

to cut a release:

1. update `CHANGES.txt` (write the entry for the version being released)
2. bump `VERSION`
3. commit, tag (no `v` prefix), push
4. run all the checks above (pytest, `make ci`, flake8, `make typecheck`)
5. build, check, upload
6. create a GitHub release

```console
$ git tag "$(cat VERSION)"   # e.g. 0.11.0
$ git push origin master "$(cat VERSION)"
$ rm -rf dist && make build  # python -m build -> dist/
$ make upload                # twine check + twine upload (needs PyPI credentials)
$ gh release create "$(cat VERSION)" --title "$(cat VERSION)" --notes "..."   # notes: the CHANGES.txt section
```

before uploading, you can smoke-test the wheel in a clean environment:

```console
$ uv venv /tmp/kamidana-check && uv pip install --python /tmp/kamidana-check dist/*.whl
$ /tmp/kamidana-check/bin/kamidana --help
```
