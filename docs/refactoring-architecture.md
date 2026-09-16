# Refactoring: architecture and design

This document organizes the architectural refactoring candidates found by
reading the whole codebase (~1000 lines). For the concrete file-by-file list,
see [refactoring-checklist.md](./refactoring-checklist.md).

## Module map

```
commands/onefile.py     kamidana        CLI: single template render
commands/manyfiles.py   kamidana-batch  CLI: batch render from a spec file
loader.py               TemplateLoader  data files + stdin + additionals -> context
driver.py               Driver / ContextDumpDriver / BatchCommandDriver
extensions/             jinja2.Extension subclasses that inject "additionals"
additionals/            user-facing filter/global/test libraries (naming, reader, env)
_path.py                template path resolution for error reporting
debug/                  gentle error rendering (traceback surgery)
listinfo.py             --list-info implementation
_import.py              minimal module/symbol importer (added; replaced magicalimport)
interfaces.py           IDriver / ITemplateLoader protocols
__init__.py             marker decorators: as_filter / as_global / as_test / as_globals_generator
```

## Data flow

```
argv -> commands/*.main()
      -> import_symbol(--loader)  -> TemplateLoader
      -> import_symbol(--driver)  -> Driver
loader.data        = deepmerge(loadfile(-d ...), stdin when -i given)
loader.additionals = deepmerge(collect_marked_items(m) for m in -a ...)
loader.load        = FileLoader-style get_source for jinja2.FunctionLoader
driver.run         = env.get_or_select_template -> render -> dumpfile
```

The pipeline is small and clean in the happy path. The fragile parts are the
plugin-loading machinery and the error-reporting path, which both reach into
interpreter/jinja2 internals.

## Design issues, in priority order

### 1. debug/ is coupled to jinja2's generated-code internals

`debug/_extract.py` classifies traceback frames by `co_name` —
`"top-level template code"`, `block '<name>'`, `"template"` — which are the
names `jinja2.debug.rewrite_traceback_stack` assigns when rewriting the
traceback of a render failure. These names are an implementation detail of
jinja2 (they changed between 2.x and 3.x: `block "x"` became `block 'x'`,
macros now appear as plain `template`). Any future jinja2 change to
`debug.py`/`compiler.py` can silently degrade output to a raw traceback.

Direction:

- Pin the heuristic to a documented jinja2 version range, and add a guard that
  falls back to the standard traceback instead of producing misleading output.
- Cover the frame-name mapping with a unit test that asserts on
  `jinja2.__version__` so an upgrade fails loudly, not silently.
- Longer term, consider hooking `jinja2.Template.render` /
  `Environment.handle_exception` or catching `TemplateError` subclasses
  instead of walking `traceback` frames — the frame-name sniffing exists only
  because the failure point must be mapped back to template source lines.

### 2. Frame introspection in the cookiecutter extension

`extensions/__init__.py::_extract_module_from_cookiecutter_cotext` walks
`inspect.currentframe().f_back` looking for locals named `context` and
`repo_dir` in cookiecutter's own frames. This breaks if cookiecutter renames
or restructures those locals, and the name lookup is not scoped to
cookiecutter's modules — any caller frame with a `context` local matches.

Direction:

- Check `f.f_code.co_filename` belongs to cookiecutter's package before
  trusting `f_locals`.
- Investigate whether newer cookiecutter passes jinja2 extension options or
  exposes the context another way; the frame walk may be unnecessary now.
- At minimum wrap the whole thing in a clearly-documented "best effort" path
  so failure produces a helpful message, and add a regression test that runs
  cookiecutter end to end (today it is only covered by
  `examples/extensions`).

Note: `Environment(optimized=False)` is now set explicitly in
`driver._make_environment`. That flag keeps the eval context unoptimized; the
frame walk above targets *cookiecutter's* frames (it runs inside
`Extension.__init__`, before rendering), but keeping `optimized=False` also
keeps jinja2's `context` reachable in template frames, which the debugging
tooling benefits from. Documented here because the coupling is non-obvious.

### 3. Hidden contract between `_path.py` and `debug/`

`_path.TemplatePath` is a `str` subclass with a monkey-patched `.original`
attribute; `XTemplatePathNotFound.original_context` re-reads it inside the
exception so that `gentleerror` can rewrite the error message from an absolute
joined path back to the path written in the template. Three artifacts —
`_TemplatePath`, `XTemplatePathNotFound.original_context`, and
`gentleerror._get_info_from_exception` (marked `xxx: remove it`) — form one
feature: "report the template path as the user wrote it".

Direction: consolidate into one small module (e.g. `kamidana/errors.py`) that
owns the path decoration, the exception, and the message rewrite, so the
feature can be tested and deleted in one place.

### 4. Lazy state via `@reify` + stdin side effects

`TemplateLoader.data` is `@reify` (cached property) and reads **stdin** on
first access when `--input-format` is set — i.e., the loader consumes stdin
the first time any template touches `data`, which is implicit and hard to see.
`additionals` is similarly lazy.

Direction: either load eagerly in `main()` (simple, predictable ordering) or
make the laziness explicit in the interface docs. This also removes the need
for `dictknife.langhelpers.reify` (`functools.cached_property` is equivalent
on Python >= 3.8).

### 5. Batch spec shape is informal

`BatchCommandDriver.load` validates required keys by hand (raising on missing
`template`/`dst`, warning on unknown keys) and documents the
`deepmerge(data, core_data)` precedence inline — command-line `-d` data wins
on scalar conflicts, lists are unioned, dicts merged recursively.

Direction: define the batch spec as a typed shape (dataclass or TypedDict)
and validate once, instead of the hand-rolled checks.

### 6. `collect_marked_items` merges by `v.__name__`

`as_filter`/`as_global`/`as_test` collect functions into
`{"filters": ..., "globals": ..., "tests": ...}` keyed by `v.__name__`, so two
modules that define the same name silently overwrite each other (deepmerge
order). `as_globals_generator` eagerly calls `v()` at collection time.

Direction: allow `@as_filter(name=...)` to override the key, and make
generator evaluation lazy (defer `v()` until the environment is built) or
document the eager behavior.

### 7. Version/changelog workflow is manual

`VERSION` file + `CHANGES.txt` are manual; consider
`hatch-vcs`/`setuptools-scm` or a `bumpversion` workflow.

## Dependency notes

Runtime deps are `jinja2>=3.1`, `dictknife[load]>=0.14`,
`inflection>=0.5` — three direct deps plus transitives `MarkupSafe`,
`ruamel.yaml`, `tomlkit`.

- `dictknife` supplies `deepmerge`, `loading` (multi-format I/O),
  `langhelpers.reify`. If the project ever wants to shed it: `reify` ->
  `functools.cached_property`; `deepmerge` is ~30 lines; but `loading`'s
  format dispatch (yaml/toml/json/csv/...) is genuinely useful and is what
  `-i/-o` are built on — keeping dictknife is reasonable.
- `magicalimport` was inlined into `kamidana/_import.py` — the used
  surface (`import_module` by path/dotted name, `import_symbol` with
  `ns`, relative imports for files inside packages) is much smaller
  than magicalimport's feature set (sys.path guessing, `expose_members`).
- `inflection` is used only for `pluralize`/`singularize` in
  `additionals/naming.py`. If minimizing further matters more than those two
  filters, they could move behind an optional extra or a tiny local
  implementation.
- `cookiecutter` is only needed by `examples/extensions`; it stays out of
  runtime deps but is installed in CI for `make ci`.

### Known upstream behavior change: yaml flow style

`dictknife>=0.14` loads yaml with `ruamel.yaml.YAML(typ="rt")` (round-trip,
quotes/flow preserved). Rendered template output like `{"name": "me"}` is
valid flow-style yaml, and the round-trip loader keeps that style on dump —
so `format: yaml` may now emit `{"name": "me"}` instead of block-style
`name: me`. If block style is wanted back, the fix belongs in dictknife
(load with `typ="safe"` for `loads()`, or normalize the parsed value before
dumping); kamidana should not reach into `ruamel.yaml.comments` to strip it.
