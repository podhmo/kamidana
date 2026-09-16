# Refactoring: file-by-file checklist

Concrete refactoring spots, file by file. Everything listed here is still
open; completed items are removed.

## kamidana/_import.py (new, replaces magicalimport)

- [ ] `import_symbol()` lost the `silent`/`here` options from
  magicalimport — unused today; re-add only if a caller needs them.
- [ ] a file inside a package is imported through the real machinery:
  its root dir stays on `sys.path` for the rest of the process — fine
  for a CLI, but a library embedding `import_module` would see the side
  effect. Standalone files (no `__init__.py` nearby) still cannot use
  relative imports — by design.

## kamidana/loader.py

- [ ] `data` reads `sys.stdin` lazily on first access (see architecture doc
  §4). Make eager in `main()` or document.
- [ ] `load()` re-reads the template file on every call — jinja2 asks the
  loader again for `{% extends %}`/`{% include %}` targets; add `mtime`-keyed
  caching if profiling shows it matters.
- [ ] `additionals` falls back `ImportError -> kamidana.additionals.<name>` —
  catches the *inner* import errors of the user module too (a buggy
  additional module that itself fails to import is retried under the
  `kamidana.additionals` namespace, producing a confusing error). Narrow to
  `ModuleNotFoundError` where `e.name` matches the requested top-level name.

## kamidana/extensions/__init__.py

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

- [ ] `Formatter.line_format` — `("{lineno: %d}: {line}" % (size))` builds a
  format string with a dynamic width via `%`-formatting; rewrite as
  f-string for readability.
- [ ] `gentleerror._get_info_from_exception` is marked `xxx: remove it` —
  fold into `errors.py` consolidation (architecture doc §3).

## kamidana/commands/

- [ ] `logging._nameToLevel` is private API — `logging.getLevelNamesMapping()`
  exists on >= 3.11; switch when the floor moves past 3.10 (3.10 EOLs Oct
  2026).
- [ ] `import_symbol` failures (a bad `--loader` path) are caught by
  `error_handler` and reported as gentle errors — good — but non-template
  exceptions re-raise a raw traceback; consider routing all errors through a
  consistent policy.

## kamidana/listinfo.py

- [ ] Discovering "additional modules" via filesystem listing of
  `kamidana.additionals` misses modules importable only via `sys.path`;
  documenting the limitation is enough.

## kamidana/__init__.py

- [ ] `collect_marked_items` keyed by `v.__name__` — name collisions between
  merged additional modules silently overwrite (architecture doc §6).
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

## Packaging / CI

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
