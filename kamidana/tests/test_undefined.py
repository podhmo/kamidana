import sys

import jinja2
import pytest

from kamidana.debug.gentleerror import translate_error
from kamidana.loader import TemplateLoader


@pytest.fixture
def loader():
    return TemplateLoader([], [], [])


def test_strict_undefined_error_shows_location(loader, tmp_path, monkeypatch):
    # https://github.com/podhmo/kamidana/issues/31
    # with StrictUndefined, using a variable that was not passed raises
    # UndefinedError, and the "gentle error" report shows where it happened.
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "t.j2").write_text("name: {{ name }}\nage: {{ age }}\n")
    env = _make_environment(
        loader.load, {}, [], undefined=jinja2.StrictUndefined
    )
    with pytest.raises(jinja2.UndefinedError) as e:
        env.get_template("./t.j2").render(name="foo")

    output = translate_error(e.value)
    assert "exception: jinja2.exceptions.UndefinedError" in output
    assert "message: 'age' is undefined" in output
    assert "where: t.j2" in output
    assert "->  2: age: {{ age }}" in output


def test_undefined_in_included_template_shows_child_frame(
    loader, tmp_path, monkeypatch
):
    # when the undefined variable is used in an included template, `where`
    # points at the included file, and both template frames are shown.
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "parent.j2").write_text('{% include "./child.j2" %}\n')
    (tmp_path / "child.j2").write_text("x: {{ missing }}\n")
    env = _make_environment(
        loader.load, {}, [], undefined=jinja2.StrictUndefined
    )
    with pytest.raises(jinja2.UndefinedError) as e:
        env.get_template("./parent.j2").render()

    output = translate_error(e.value)
    assert "where: child.j2" in output
    assert "child.j2:" in output
    assert "parent.j2:" in output
    assert "->  1: x: {{ missing }}" in output


def test_default_is_jinja2_undefined(loader, tmp_path, monkeypatch):
    # like jinja2 itself, an undefined variable renders as empty by default
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "t.j2").write_text("age: {{ age }}\n")
    env = _make_environment(loader.load, {}, [])
    assert env.undefined is jinja2.Undefined
    assert env.get_template("./t.j2").render() == "age: "


def test_undefined_debug_renders_placeholder(loader, tmp_path, monkeypatch):
    from kamidana.driver import _make_environment

    monkeypatch.chdir(tmp_path)
    (tmp_path / "t.j2").write_text("age: {{ age }}\n")
    env = _make_environment(
        loader.load, {}, [], undefined=jinja2.DebugUndefined
    )
    assert env.get_template("./t.j2").render() == "age: {{ age }}"


def test_driver_is_undefined_by_default(loader, tmp_path, monkeypatch):
    from kamidana.driver import Driver

    monkeypatch.chdir(tmp_path)
    (tmp_path / "t.j2").write_text("age: {{ age }}\n")
    driver = Driver(loader, "raw")
    assert driver.environment.undefined is jinja2.Undefined


def test_driver_honors_undefined_attribute(loader, tmp_path, monkeypatch):
    from kamidana.driver import Driver

    monkeypatch.chdir(tmp_path)
    (tmp_path / "t.j2").write_text("age: {{ age }}\n")
    driver = Driver(loader, "raw")
    driver.undefined = jinja2.StrictUndefined
    assert driver.environment.undefined is jinja2.StrictUndefined
    with pytest.raises(jinja2.UndefinedError):
        driver.run("./t.j2", None)


def test_cli_strict_undefined_option(tmp_path, monkeypatch, capsys):
    # the --strict-undefined option must be passable from the cli
    from kamidana.commands.onefile import main

    monkeypatch.chdir(tmp_path)
    (tmp_path / "t.j2").write_text("name: {{ name }}\nage: {{ age }}\n")
    (tmp_path / "data.yaml").write_text("name: foo\n")

    # default: the missing variable renders as empty (jinja2.Undefined)
    monkeypatch.setattr(
        sys, "argv", ["kamidana", "-d", "data.yaml", "./t.j2"]
    )
    main()
    assert capsys.readouterr().out == "name: foo\nage: \n"

    # --strict-undefined: fails with a gentle error showing the location
    monkeypatch.setattr(
        sys,
        "argv",
        ["kamidana", "-d", "data.yaml", "--strict-undefined", "./t.j2"],
    )
    with pytest.raises(SystemExit):
        main()
    err = capsys.readouterr().err
    assert "exception: jinja2.exceptions.UndefinedError" in err
    assert "where: t.j2" in err
    assert "->  2: age: {{ age }}" in err


def test_cli_batch_strict_undefined_option(tmp_path, monkeypatch, capsys):
    from kamidana.commands.manyfiles import main

    monkeypatch.chdir(tmp_path)
    (tmp_path / "t.j2").write_text("name: {{ name }}\nage: {{ age }}\n")
    (tmp_path / "batch.yaml").write_text(
        "- template: ./t.j2\n"
        "  dst: out.txt\n"
        "  data:\n"
        "    name: foo\n"
    )

    # default: the missing variable renders as empty
    monkeypatch.setattr(
        sys, "argv", ["kamidana-batch", "batch.yaml"]
    )
    main()
    assert (tmp_path / "out.txt").read_text() == "name: foo\nage: \n"

    # --strict-undefined: fails with a gentle error
    monkeypatch.setattr(
        sys,
        "argv",
        ["kamidana-batch", "--strict-undefined", "batch.yaml"],
    )
    with pytest.raises(SystemExit):
        main()
    assert "jinja2.exceptions.UndefinedError" in capsys.readouterr().err
