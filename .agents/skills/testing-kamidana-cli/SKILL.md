---
name: testing-kamidana-cli
description: End-to-end testing of kamidana CLI imports, template rendering, and error diagnostics in isolated scratch directories.
---

# Testing kamidana CLI

- Use the session's prepared virtualenv or an explicitly selected interpreter.
  Confirm its `kamidana.__file__` points at the checkout before testing; a system
  Python may have different or missing editable-install dependencies.
- Keep fixture packages, templates, execution counters, and transcripts outside
  the repository so example regeneration and clean-tree checks remain reliable.
- Filesystem template arguments must begin with `./`, `../`, or `/`. A bare
  template filename is interpreted as a package resource, not a cwd file.
- Register added callables with `kamidana.as_filter` and `kamidana.as_global`.
  Invoke additions using repeated `-a file.py` options. Custom loaders use
  `--loader file.py:ClassName` and can subclass `kamidana.loader.TemplateLoader`.
- Package relative-import fixtures need `__init__.py` in each package directory.
  Check nested imports and run from both outside and inside the package.
- To verify import deduplication end-to-end, render a global that checks module
  object identity, and count module-body executions with a scratch marker.
- Include competing package roots both absent from and already later in
  `PYTHONPATH`; these exercise different import-path ordering behavior.
- For error UX, capture stdout, stderr, and exit status separately. Normal errors
  should exit 1 and identify the user's original failure location — a missing
  `.py` file reports `module not found: x.py (also tried kamidana.additionals.x)`
  while an existing file that fails at import surfaces its own error with
  `where:` and a user-frame traceback. Compare `--debug` output to identify the
  original cause; do not count debug-only visibility as a passing normal-mode
  UX check.
- Use variable-driven filters (e.g. `{{ value | boom }}` with `-d data.json`) to
  ensure exceptions happen during rendering rather than constant folding.
- Shell-only CLI tests need exact command/output transcripts, not idle-desktop
  recordings. Save fixture/reproduction scripts alongside transcripts.

## Devin Secrets Needed

None for local CLI testing.
