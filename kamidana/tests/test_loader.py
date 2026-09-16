import pytest

from kamidana.loader import TemplateLoader
from kamidana._path import XTemplatePathNotFound


@pytest.fixture
def loader():
    return TemplateLoader([], [], [])


@pytest.fixture
def package(tmp_path, monkeypatch):
    pkg = tmp_path / "mypkg"
    (pkg / "templates" / "sub").mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "templates" / "hello.j2").write_text("hello\n")
    (pkg / "templates" / "sub" / "page.j2").write_text(
        'page {% include "../hello.j2" %}'
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    return pkg


def test_load_physical_path(loader, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "hello.j2").write_text("hello\n")
    source, filename, _ = loader.load("./hello.j2")
    assert source == "hello\n"


def test_load_physical_path_not_found(loader, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(XTemplatePathNotFound):
        loader.load("./notfound.j2")


def test_bare_name_is_package_spec(loader, tmp_path, monkeypatch):
    # a name without './' or '/' prefix is a package template spec, so a
    # file in the current directory needs an explicit "./" prefix.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "hello.j2").write_text("hello\n")
    with pytest.raises(XTemplatePathNotFound) as e:
        loader.load("hello.j2")
    assert '"./hello.j2"' in str(e.value)


def test_load_from_package(loader, package):
    source, filename, _ = loader.load("mypkg/templates/hello.j2")
    assert source == "hello\n"


def test_load_from_package_not_found(loader, tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(XTemplatePathNotFound) as e:
        loader.load("nosuchpkg/templates/hello.j2")
    assert 'package "nosuchpkg" is not found' in str(e.value)


def test_load_from_package_resource_not_found(loader, package):
    with pytest.raises(XTemplatePathNotFound) as e:
        loader.load("mypkg/templates/notfound.j2")
    assert '"templates/notfound.j2" is not found in package "mypkg"' in str(e.value)


def test_join_path_in_package(loader, package):
    # {% extends %}/{% include %} are resolved relative to the parent
    # template, also inside a package.
    from kamidana.driver import _make_environment

    env = _make_environment(loader.load, {}, [])
    t = env.get_template("mypkg/templates/sub/page.j2")
    assert t.render() == "page hello"
