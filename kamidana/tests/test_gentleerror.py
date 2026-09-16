import textwrap

import pytest

from kamidana._path import XTemplatePathNotFound
from kamidana.debug.gentleerror import translate_error
from kamidana.loader import TemplateLoader


@pytest.fixture
def loader():
    return TemplateLoader([], [], [])


def test_direct_not_found_omits_where(loader, tmp_path, monkeypatch):
    # regression: https://github.com/podhmo/kamidana/issues/61
    monkeypatch.chdir(tmp_path)
    with pytest.raises(XTemplatePathNotFound) as e:
        loader.load("./no-such.html")
    output = translate_error(e.value)
    assert "exception: kamidana._path.XTemplatePathNotFound" in output
    assert "no-such.html" in output
    assert "where:" not in output


def test_include_not_found_shows_parent_in_where(loader, tmp_path, monkeypatch):
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


def test_deep_chain_shows_all_template_frames(loader, tmp_path, monkeypatch):
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

    def money(amount):
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


def test_same_file_macro_keeps_caller_frame(loader, tmp_path, monkeypatch):
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

    def money(amount):
        raise KeyError("JPY")

    env = _make_environment(loader.load, {"filters": {"money": money}}, [])
    with pytest.raises(KeyError) as e:
        env.get_template("./samemacro.html").render()

    output = translate_error(e.value)
    assert output.count("samemacro.html:") == 2
    assert "->  4: {{ price() }}" in output
    assert "->  2:   price: {{ 100|money }}" in output


def test_python_side_error_where_points_at_raise_site(
    loader, tmp_path, monkeypatch
):
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
    import helpers

    def money(amount):
        return helpers.format_money(amount, "JPY")

    env = _make_environment(loader.load, {"filters": {"money": money}}, [])
    with pytest.raises(KeyError) as e:
        env.get_template("./main.jinja2").render()
    output = translate_error(e.value)
    lineno = helpers.lookup_rate.__code__.co_firstlineno + 1
    assert "where: helpers.py:{}".format(lineno) in output
    assert "where: main.jinja2" not in output
