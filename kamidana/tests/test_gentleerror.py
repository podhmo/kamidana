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
