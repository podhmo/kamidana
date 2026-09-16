# Refactoring: file-by-file checklist

Concrete refactoring spots, file by file. `done` marks items already addressed
in the dependency-update change; the rest are open.

## kamidana/_import.py (new, replaces magicalimport)

- [ ] `_module_id()` can collide: `a/b.py` and `a_b.py` both map to `a.b`.
  Also `sys.modules` keys like `src_00inheritance.url_for` leak into the
  global module table — consider a private registry dict instead of
  `sys.modules`, or a hashed suffix.
- [ ] `import_symbol()` loses `silent`/`here`/`sep` options from
  magicalimport — unused today; re-add only if a caller needs them.
- [ ] `import_module()` does not create parent-package `__init__` modules the
  way magicalimport did; an additional file inside a package directory that
  uses relative imports will fail. Acceptable for standalone `*.py`
  additionals — document the limitation.

## kamidana/loader.py

- [ ] `data` reads `sys.stdin` lazily on first access (see architecture doc
  §5). Make eager in `main()` or document.
- [ ] `load()` re-reads the template file on every call — jinja2 asks the
  loader again for `{% extends %}`/`{% include %}` targets; add `mtime`-keyed
  caching if profiling shows it matters.
- [ ] `additionals` falls back `ImportError -> kamidana.additionals.<name>` —
  catches the *inner* import errors of the user module too (a buggy
  additional module that itself fails to import is retried under the
  `kamidana.additionals` namespace, producing a confusing error). Narrow to
  `ModuleNotFoundError` where `e.name` matches the requested top-level name.

## kamidana/driver.py

- [x] `optimized=False` now set explicitly (required assumption for template
  frame introspection).
- [x] `BaseDriver` extracted: owns `loader`/`format`/`environment` plus a
  shared `run` (`dump(transform(load(src)), dst)`); `Driver.transform`
  renders, `ContextDumpDriver.transform` builds the context dict,
  `BatchCommandDriver` uses the identity default.
- [x] `BatchCommandDriver.self.cache` removed (real cache is the local
  `cache` in `load()`).
- [x] `BatchCommandDriver.load()` — non-dict commands and missing
  `template`/`dst` raise; unknown keys log a warning; the
  `deepmerge(data, core_data)` precedence is documented (addtoset: lists
  unioned, dicts merged recursively, CLI `-d` data wins on scalar
  conflicts).
- [x] `dump()` — comment added that `cmd["dst"]` is joined under `outdir`
  without sanitizing `..` (trusted input for a user-run CLI).
- [x] `-o raw` centralized: module-level `RAW_FORMAT` constant plus
  `_load_for_dump()` helper cover all three `dump` methods
  (`ContextDumpDriver` still maps raw -> json since it dumps a dict).

## kamidana/extensions/__init__.py

- [x] `logging.Logger(__name__)` -> `logging.getLogger(__name__)` (the module
  logger was never attached to the logging hierarchy, so `logger.info` was
  dead output).
- [ ] `_extract_module_from_cookiecutter_cotext` — frame-local sniffing; see
  architecture doc §2. Also fix the `cotext` typo in the name while keeping a
  deprecated alias if needed.
- [ ] `create_apply_additonal_modules_extension_class` — typo `additonal` in
  a public-ish helper name; class is created via `type()` solely to inject
  `__init__` + `__doc__` — a comment explaining why a normal subclass does not
  suffice (extension identity must be unique per modules list) would help.
- [ ] `j2utils.import_string` is a semi-private jinja2 helper — trivially
  replaceable (`importlib.import_module` + `getattr`).

## kamidana/debug/

- [x] `_extract.py` rewritten for jinja2 3.x frame names
  (`block '<name>'`/`template`/`top-level template code`) — was silently
  misclassifying block frames as python and dropping sections from the error
  output.
- [x] jinja2-internal tail check no longer sniffs `"site-packages/jinja2"`
  substrings; compares against `jinja2.__file__`'s directory.
- [ ] `Formatter.line_format` — `("{lineno: %d}: {line}" % (size))` builds a
  format string with a dynamic width via `%`-formatting; rewrite as
  f-string for readability.
- [ ] `gentleerror._get_info_from_exception` is marked `xxx: remove it` —
  fold into `errors.py` consolidation (architecture doc §3).
- [ ] `color.is_colorful` tests `sys.stdout.isatty()` but all callers print to
  stderr — should test `sys.stderr`.
- [ ] No unit tests for `debug/` at all — coverage is only the examples
  fixtures. Extract golden cases into `kamidana/tests/` so jinja2 upgrades
  fail in `pytest`, not only in `make ci`.

## kamidana/commands/

- [ ] Duplicated parser/prologue between `onefile.py` and `manyfiles.py`
  (architecture doc §6).
- [ ] `logging._nameToLevel` is private API — `logging.getLevelNamesMapping()`
  exists on >= 3.11; switch when the floor moves past 3.10 (3.10 EOLs Oct
  2026).
- [ ] `onefile.py` `--list-info` writes a hardcoded `\x1b[1m` ANSI bold header
  to stderr without checking `is_colorful()`.
- [ ] `import_symbol` failures (a bad `--loader` path) are caught by
  `error_handler` and reported as gentle errors — good — but non-template
  exceptions re-raise a raw traceback; consider routing all errors through a
  consistent policy.

## kamidana/listinfo.py

- [x] `importlib_resources.contents` -> `importlib.resources.files().iterdir()`
  (`contents()` is deprecated; the backport package is gone entirely).
- [x] `OrderedDict` -> plain `dict` (ordered since 3.7).
- [x] `inspect.getdoc(cls)` can return `None` -> `None.strip()` would crash on
  an undocumented extension class (none today; cheap guard).
- [ ] Discovering "additional modules" via filesystem listing of
  `kamidana.additionals` misses modules importable only via `sys.path`;
  documenting the limitation is enough.

## kamidana/__init__.py

- [ ] `collect_marked_items` keyed by `v.__name__` — name collisions between
  merged additional modules silently overwrite (architecture doc §8).
- [ ] `MARKER_TAG`/`IS_GENERATOR_TAG` attributes written onto foreign
  functions (e.g. `inflection.pluralize`) mutate third-party objects;
  wrapping instead of tagging would avoid surprises if a shared function
  object were tagged differently elsewhere.

## kamidana/_path.py

- [ ] `str` subclass with a patched-on `.original` attribute — works because
  jinja2 keeps the object intact through `join_path`/`get_template`; fragile
  if jinja2 ever reconstructs the path. Covered by the include-404 fixtures;
  add a comment in `_path.py` pointing at the coupling.

## kamidana/additionals/

- [ ] `naming.snakecase` hand-rolls `underscore` differently from
  `inflection.underscore` — decide whether to delegate (behavior differs on
  `kebab-case` input, so check fixtures before changing).
- [ ] `env.env()` is registered both as filter and global under the name
  `env` — name is fine but shadows nothing in templates; no change needed,
  just note it relies on the same-name registration working.
- [ ] `reader.read_from_command` runs `shell=True` on template-supplied
  commands — by design (a templating tool), but worth a docstring note that
  templates are trusted input.

## kamidana/tests/

- [ ] Only `test_naming.py` exists. Port the error-output examples
  (`examples/basic/src/01*`, `04*`, `05*`) into pytest golden tests so the
  gentle-error output is checked without `make`.

## Packaging / CI

- [x] `setup.py`: `python_requires=">=3.10"`, deps trimmed to
  `jinja2>=3.1`, `dictknife[load]>=0.14`, `inflection>=0.5`; dropped
  `fastentrypoints`, `importlib_resources`, `tests_require`, `test_suite`.
- [x] `setup.cfg` `[bdist_wheel] universal=1` removed (py3-only).
- [x] `docs` extras: dropped `recommonmark` (dead; no `.md` sources); conf.py
  updated (`html_theme_path` removed — deprecated with modern
  sphinx_rtd_theme; version read from `VERSION`).
- [x] CI matrix: `3.9/3.10/3.11` -> `3.10–3.14`; actions checkout@v5 /
  setup-python@v6; `make ci` added so the examples fixtures actually gate CI
  (they were previously local-only).
- [x] `Makefile` `MASK` now also normalizes `, line N,` inside site-packages
  frames and strips PEP 657 `~~~~^^^^` caret lines — jinja2 internals line
  numbers drift between releases and traceback carets differ between Python
  3.10 and >= 3.11, both of which broke the fixtures.
- [x] Moved to `pyproject.toml`; `VERSION` is read via
  `tool.setuptools.dynamic.version.file` and `README.md` + `CHANGES.txt`
  form the `text/markdown` `readme`.
- [ ] `Makefile ci`'s `test -z $(git diff)` fails on *any* dirty file, not
  just regenerated outputs — in CI this is fine after a clean checkout, but
  locally it conflates working changes with fixture drift. Consider scoping
  the diff to `examples/*/dst`.
- [ ] Python 3.10 EOL is 2026-10 — bump `python_requires` floor to 3.11 and
  drop 3.10 from the matrix then.

## Deliberately left alone

- `inflection` kept (zero-dep, used by `pluralize`/`singularize` filters —
  removing it deletes features; see architecture doc for the option).
- `dictknife` kept (`loading` multi-format I/O is core functionality).
- `VERSION` bump, README regeneration, `CHANGES.txt` entry are part of this
  change but a real release can regroup them.
