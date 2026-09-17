from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from kamidana.loader import TemplateLoader
from kamidana._path import XTemplatePathNotFound

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def loader() -> TemplateLoader:
    return TemplateLoader([], [], [])


@pytest.fixture
def package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    pkg = tmp_path / "mypkg"
    (pkg / "templates" / "sub").mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "templates" / "hello.j2").write_text("hello\n")
    (pkg / "templates" / "sub" / "page.j2").write_text(
        'page {% include "../hello.j2" %}'
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    return pkg


def test_load_physical_path(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "hello.j2").write_text("hello\n")
    source, filename, _ = loader.load("./hello.j2")
    assert source == "hello\n"


def test_load_physical_path_not_found(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(XTemplatePathNotFound):
        loader.load("./notfound.j2")


def test_bare_name_is_package_spec(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # a name without './' or '/' prefix is a package template spec, so a
    # file in the current directory needs an explicit "./" prefix.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "hello.j2").write_text("hello\n")
    with pytest.raises(XTemplatePathNotFound) as e:
        loader.load("hello.j2")
    assert '"./hello.j2"' in str(e.value)


def test_load_from_package(loader: TemplateLoader, package: Path) -> None:
    source, filename, _ = loader.load("mypkg/templates/hello.j2")
    assert source == "hello\n"


def test_load_from_package_not_found(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(tmp_path))
    with pytest.raises(XTemplatePathNotFound) as e:
        loader.load("nosuchpkg/templates/hello.j2")
    assert 'package "nosuchpkg" is not found' in str(e.value)


def test_load_from_package_resource_not_found(
    loader: TemplateLoader, package: Path
) -> None:
    with pytest.raises(XTemplatePathNotFound) as e:
        loader.load("mypkg/templates/notfound.j2")
    assert '"templates/notfound.j2" is not found in package "mypkg"' in str(e.value)


def test_additionals_from_file_path(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "myfilter.py").write_text(
        "from kamidana import as_filter\n\n\n@as_filter\ndef shout(s):\n"
        "    return s.upper()\n"
    )
    loader.additional_path_list.append("myfilter.py")
    assert loader.additionals["filters"]["shout"]("hi") == "HI"


def test_additionals_fallback_to_package_module(
    loader: TemplateLoader,
) -> None:
    # '-a naming' resolves to the bundled kamidana.additionals.naming module.
    loader.additional_path_list.append("naming")
    assert "snakecase" in loader.additionals["filters"]


def test_additionals_missing_py_module(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # the fallback module name must not keep the '.py' suffix, otherwise it
    # is looked up as a file path and the error message is confusing.
    monkeypatch.chdir(tmp_path)
    loader.additional_path_list.append("missing.py")
    with pytest.raises(ImportError) as e:
        loader.additionals
    assert "missing.py" in str(e.value)
    assert "kamidana.additionals.missing" in str(e.value)
    assert "kamidana.additionals.missing.py" not in str(e.value)


def test_additionals_existing_file_error_is_not_masked(
    loader: TemplateLoader, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # a ".py" file that exists but fails to import must surface its own
    # error, not a "module not found" message for the builtin fallback.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "missing.py").write_text("import nosuchdep_xyz\n")
    loader.additional_path_list.append("missing.py")
    with pytest.raises(ImportError) as e:
        loader.additionals
    assert "nosuchdep_xyz" in str(e.value)
    assert "kamidana.additionals" not in str(e.value)


def test_data_from_json_literal() -> None:
    loader = TemplateLoader([("json", {"user_name": "world"})], [], [])
    assert loader.data == {"user_name": "world"}


def test_data_json_overrides_file(tmp_path: Path) -> None:
    # ("file", ...) then ("json", ...): the later entry wins.
    (tmp_path / "a.yaml").write_text("x: 1\ny: 2\n")
    loader = TemplateLoader(
        [("file", str(tmp_path / "a.yaml")), ("json", {"x": 10})], [], []
    )
    assert loader.data == {"x": 10, "y": 2}


def test_data_file_overrides_json(tmp_path: Path) -> None:
    # the reverse order: the file wins.
    (tmp_path / "a.yaml").write_text("x: 1\ny: 2\n")
    loader = TemplateLoader(
        [("json", {"x": 10, "z": 3}), ("file", str(tmp_path / "a.yaml"))], [], []
    )
    assert loader.data == {"x": 1, "y": 2, "z": 3}


def test_data_plain_path_is_a_file(tmp_path: Path) -> None:
    # a bare string entry is treated as a data file path.
    (tmp_path / "a.yaml").write_text("x: 1\n")
    loader = TemplateLoader([str(tmp_path / "a.yaml")], [], [])
    assert loader.data == {"x": 1}


def test_data_stdin_keeps_final_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import io

    (tmp_path / "a.yaml").write_text("x: 1\n")
    monkeypatch.setattr("sys.stdin", io.StringIO('{"x": 99}'))
    loader = TemplateLoader(
        [("file", str(tmp_path / "a.yaml")), ("json", {"x": 5, "z": 3})],
        [],
        [],
        format="json",
    )
    assert loader.data == {"x": 99, "z": 3}


def test_join_path_in_package(loader: TemplateLoader, package: Path) -> None:
    # {% extends %}/{% include %} are resolved relative to the parent
    # template, also inside a package.
    from kamidana.driver import _make_environment

    env = _make_environment(loader.load, {}, [])
    t = env.get_template("mypkg/templates/sub/page.j2")
    assert t.render() == "page hello"
