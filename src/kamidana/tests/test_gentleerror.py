from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

import pytest

from kamidana._path import XTemplatePathNotFound
from kamidana.debug.gentleerror import translate_error
from kamidana.loader import TemplateLoader

if TYPE_CHECKING:
    import typing as t
    from pathlib import Path


@pytest.fixture
def loader() -> TemplateLoader:
    return TemplateLoader([], [], [])


def test_direct_not_found_omits_where(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # regression: https://github.com/podhmo/kamidana/issues/61
    monkeypatch.chdir(tmp_path)
    with pytest.raises(XTemplatePathNotFound) as e:
        loader.load("./no-such.html")
    output = translate_error(e.value)
    assert "exception: kamidana._path.XTemplatePathNotFound" in output
    assert "no-such.html" in output
    assert "where:" not in output


def test_include_not_found_shows_parent_in_where(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # when a template is included/extended from another template, `where`
    # points at the template that referenced the missing one.
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "parent.j2").write_text('{% include "./missing.j2" %}')
    env = _make_environment(loader.load, {}, [])
    with pytest.raises(XTemplatePathNotFound) as e:
        env.get_template("./parent.j2").render()
    output = translate_error(e.value)
    assert "where: parent.j2" in output


def test_deep_chain_shows_all_template_frames(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # regression: https://github.com/podhmo/kamidana/issues/63
    # a chain deeper than 5 frames was silently truncated to the last 5,
    # losing the head of the chain (the template the user invoked).
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "base.html").write_text(
        '<html>\n{% block content %}\n{% include "./part1.html" %}'
        "\n{% endblock %}\n</html>\n"
    )
    (tmp_path / "c2.html").write_text(
        '{% extends "base.html" %}\n'
        "{% block content %}[c2] {{ super() }}{% endblock %}\n"
    )
    (tmp_path / "c1.html").write_text(
        '{% extends "c2.html" %}\n'
        "{% block content %}[c1] {{ super() }}{% endblock %}\n"
    )
    (tmp_path / "c0.html").write_text(
        '{% extends "c1.html" %}\n'
        "{% block content %}[c0] {{ super() }}{% endblock %}\n"
    )
    (tmp_path / "part1.html").write_text(
        '<div>\n{% include "./part2.html" %}\n</div>\n'
    )
    (tmp_path / "part2.html").write_text(
        '{% import "./macros.html" as m %}\n{{ m.price() }}\n'
    )
    (tmp_path / "macros.html").write_text(
        "{% macro price() %}\n  price: {{ 100|money }}\n{% endmacro %}\n"
    )

    def money(amount: t.Any) -> t.NoReturn:
        raise KeyError("JPY")

    env = _make_environment(loader.load, {"filters": {"money": money}}, [])
    with pytest.raises(KeyError) as e:
        env.get_template("./c0.html").render()

    output = translate_error(e.value)
    for name in [
        "c0.html",
        "c1.html",
        "c2.html",
        "base.html",
        "part1.html",
        "part2.html",
        "macros.html",
    ]:
        assert "{}:".format(name) in output

    # an explicit cap still truncates, but reports what was dropped
    output = translate_error(e.value, level=5)
    assert "macros.html:" in output
    assert "c0.html:" not in output
    assert "frames omitted" in output


def test_same_file_macro_keeps_caller_frame(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # regression: https://github.com/podhmo/kamidana/issues/64
    # when a macro is defined and called in the same template file, the
    # caller-side frame (the `{{ price() }}` line) must be shown along with
    # the macro body frame that raised.
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "samemacro.html").write_text(
        "{% macro price() %}\n"
        "  price: {{ 100|money }}\n"
        "{% endmacro %}\n"
        "{{ price() }}\n"
    )

    def money(amount: t.Any) -> t.NoReturn:
        raise KeyError("JPY")

    env = _make_environment(loader.load, {"filters": {"money": money}}, [])
    with pytest.raises(KeyError) as e:
        env.get_template("./samemacro.html").render()

    output = translate_error(e.value)
    assert output.count("samemacro.html:") == 2
    assert "->  4: {{ price() }}" in output
    assert "->  2:   price: {{ 100|money }}" in output


def test_mutual_include_same_file_shown_once(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # regression: https://github.com/podhmo/kamidana/issues/65
    # the entry template keeps its literal CLI path ("./ping.html") while
    # includes resolve to absolute paths, so the same file used to appear
    # twice in the frame list.
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "ping.html").write_text('{% include "./pong.html" %}\n')
    (tmp_path / "pong.html").write_text('{% include "./ping.html" %}\n')

    env = _make_environment(loader.load, {}, [])
    with pytest.raises(RecursionError) as e:
        env.get_template("./ping.html").render()

    output = translate_error(e.value)
    assert output.count("ping.html:") == 1
    assert output.count("pong.html:") == 1


def test_stdlib_raise_where_falls_back_to_template_frame(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # regression: https://github.com/podhmo/kamidana/issues/72
    # a RecursionError raised inside frozen stdlib internals made `where`
    # point at "<frozen posixpath>:NN"; the actionable site is the
    # recursive `{% include %}` in the template.
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "loop.html").write_text(
        '<div>\n{% include "./loop.html" %}\n</div>\n'
    )

    env = _make_environment(loader.load, {}, [])
    with pytest.raises(RecursionError) as e:
        env.get_template("./loop.html").render()

    output = translate_error(e.value)
    (where_line,) = [l for l in output.splitlines() if l.startswith("where:")]
    assert where_line == "where: loop.html"


def test_python_side_error_where_points_at_raise_site(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # regression: https://github.com/podhmo/kamidana/issues/60
    # when the exception is raised inside python code (e.g. a filter),
    # `where` points at the raise site, not the template call site.
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "main.jinja2").write_text("- apple: {{ 100|money }}\n")
    (tmp_path / "helpers.py").write_text(
        textwrap.dedent(
            '''\
            _RATES = {"USD": 1.0, "EUR": 1.1}


            def lookup_rate(currency):
                return _RATES[currency]


            def format_money(amount, currency):
                rate = lookup_rate(currency)
                return "{} {}".format(round(amount * rate, 2), currency)
            '''
        )
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    import helpers  # type: ignore[import-not-found]

    def money(amount: t.Any) -> t.Any:
        return helpers.format_money(amount, "JPY")

    env = _make_environment(loader.load, {"filters": {"money": money}}, [])
    with pytest.raises(KeyError) as e:
        env.get_template("./main.jinja2").render()
    output = translate_error(e.value)
    lineno = helpers.lookup_rate.__code__.co_firstlineno + 1
    assert "where: helpers.py:{}".format(lineno) in output
    assert "where: main.jinja2" not in output


def test_python_only_error_is_rendered_gently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # an additional module that fails *while being imported* has no
    # template frames; it used to escape as a raw interpreter traceback.
    # it should now get the same exception/message/where treatment.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bad.py").write_text("raise RuntimeError('boom')\n")

    def run() -> None:
        from kamidana._import import import_module

        import_module("bad.py")

    with pytest.raises(RuntimeError) as e:
        run()

    output = translate_error(e.value)
    assert "exception: builtins.RuntimeError" in output
    assert "message: boom" in output
    assert "where: bad.py:1" in output
    assert "bad.py:" in output
    # internal frames are not `where` candidates, but they stay in the
    # Traceback: body so the raise site is never lost (#87)
    assert "_import.py" in output


def test_python_only_error_without_actionable_frames_falls_back(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # when every frame is inside stdlib/jinja2/kamidana internals there
    # is nothing actionable to point at; the full traceback is kept.
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ModuleNotFoundError) as e:
        from kamidana._import import import_module

        import_module("not-there.py")

    output = translate_error(e.value)
    assert "exception: builtins.ModuleNotFoundError" in output
    assert "not-there.py" in output
    assert "Traceback:" in output
    # `where` still names the raise site (internal, but real) (#87)
    (where_line,) = [l for l in output.splitlines() if l.startswith("where:")]
    assert "_import.py" in where_line


def test_python_only_error_keeps_stdlib_raise_site_in_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # regression: https://github.com/podhmo/kamidana/issues/87
    # an additional module failing inside stdlib used to show only the
    # user's call site; the frame that actually raised (json/decoder.py)
    # was filtered out of the traceback.
    import json

    monkeypatch.chdir(tmp_path)
    (tmp_path / "stdlib_broken.py").write_text(
        'import json\njson.loads("{broken")\n'
    )

    def run() -> None:
        from kamidana._import import import_module

        import_module("stdlib_broken.py")

    with pytest.raises(json.JSONDecodeError) as e:
        run()

    output = translate_error(e.value)
    assert "where: stdlib_broken.py:2" in output
    assert "decoder.py" in output  # the real raise site


def test_python_only_error_all_internal_where_points_at_raise_site() -> None:
    # regression: https://github.com/podhmo/kamidana/issues/87
    # when every traceback frame is internal (stdlib/site-packages),
    # `where` used to be omitted entirely; it now falls back to the
    # innermost frame -- the actual raise site.
    import json

    def run() -> None:
        json.loads("{broken")

    with pytest.raises(json.JSONDecodeError) as e:
        run()

    output = translate_error(e.value)
    (where_line,) = [l for l in output.splitlines() if l.startswith("where:")]
    assert "decoder.py" in where_line
