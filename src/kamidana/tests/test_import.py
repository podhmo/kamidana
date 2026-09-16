from __future__ import annotations

import sys
import textwrap
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

from kamidana._import import import_module, import_symbol

if TYPE_CHECKING:
    import typing as t
    from pathlib import Path


@pytest.fixture(autouse=True)
def _isolate_import_state() -> t.Iterator[None]:
    # importing by path mutates sys.path / sys.modules; restore both.
    path_before = sys.path[:]
    modules_before = set(sys.modules)
    yield
    sys.path[:] = path_before
    for name in set(sys.modules) - modules_before:
        del sys.modules[name]


def test_dotted_name_goes_through_importlib() -> None:
    m = import_module("kamidana.interfaces")
    assert m.__name__ == "kamidana.interfaces"


def test_standalone_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "foo.py").write_text("VALUE = 42\n")
    m = import_module("foo.py")
    assert m.VALUE == 42
    # __file__ (and co_filename) keeps the path as written so that
    # tracebacks show it relative.
    assert m.__file__ == "foo.py"


def test_standalone_file_code_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "foo.py").write_text("def f():\n    return 1\n")
    m = import_module("./foo.py")
    assert m.f.__code__.co_filename == "./foo.py"


def test_same_module_for_same_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "foo.py").write_text("VALUE = 1\n")
    assert import_module("foo.py") is import_module("foo.py")
    # the cache is keyed on the real path, not the written spelling
    assert import_module("foo.py") is import_module("./foo.py")


def test_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ModuleNotFoundError):
        import_module("nothere.py")


def test_cwd_false_requires_here(tmp_path: Path) -> None:
    (tmp_path / "foo.py").write_text("VALUE = 1\n")
    with pytest.raises(ValueError):
        import_module("foo.py", cwd=False)


def test_here_resolves_base_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # regardless of cwd, here= anchors relative paths
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "foo.py").write_text("VALUE = 7\n")
    monkeypatch.chdir("/")
    m = import_module("foo.py", here=str(tmp_path / "sub"))
    assert m.VALUE == 7


def test_module_name_collision_with_existing_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # "a/b.py" maps to the readable name "a.b"; when that name is already
    # taken by an unrelated module, the file gets a different name
    # instead of clobbering or returning the wrong module.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b.py").write_text("MARKER = 'file'\n")

    sentinel = ModuleType("a.b")
    monkeypatch.setitem(sys.modules, "a.b", sentinel)

    m = import_module("a/b.py")
    assert m.MARKER == "file"
    assert m.__name__ != "a.b"
    assert sys.modules["a.b"] is sentinel


def test_module_name_collision_between_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # "x/a/b.py" and "x_a/b.py" share the readable name "x_a.b"; both
    # must still be importable as distinct modules.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "x" / "a").mkdir(parents=True)
    (tmp_path / "x" / "a" / "b.py").write_text("MARKER = 'nested'\n")
    (tmp_path / "x_a").mkdir()
    (tmp_path / "x_a" / "b.py").write_text("MARKER = 'flat'\n")

    nested = import_module("x/a/b.py")
    flat = import_module("x_a/b.py")
    assert nested.MARKER == "nested"
    assert flat.MARKER == "flat"
    assert nested is not flat
    assert nested.__name__ != flat.__name__


def test_failed_import_is_not_cached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "bad.py"
    target.write_text("raise RuntimeError('boom')\n")
    with pytest.raises(RuntimeError):
        import_module("bad.py")

    target.write_text("VALUE = 3\n")
    m = import_module("bad.py")
    assert m.VALUE == 3


def test_package_member_supports_relative_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "util.py").write_text("def helper():\n    return 'help'\n")
    (pkg / "feature.py").write_text(
        textwrap.dedent(
            """\
            from . import util
            from .util import helper


            def run():
                return helper() + ':' + util.helper()
            """
        )
    )

    m = import_module("mypkg/feature.py")
    assert m.run() == "help:help"
    assert m.__name__ == "mypkg.feature"
    assert m.__package__ == "mypkg"
    # imported through the real machinery, so it is registered normally
    assert sys.modules["mypkg.feature"] is m


def test_package_member_supports_nested_subpackage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    sub = tmp_path / "mypkg" / "sub"
    sub.mkdir(parents=True)
    (tmp_path / "mypkg" / "__init__.py").write_text("")
    (sub / "__init__.py").write_text("")
    (sub / "deep.py").write_text("VALUE = 'deep'\n")
    (tmp_path / "mypkg" / "feature.py").write_text(
        "from .sub import deep\nVALUE = deep.VALUE\n"
    )

    m = import_module("mypkg/feature.py")
    assert m.VALUE == "deep"
    assert sys.modules["mypkg.sub.deep"].VALUE == "deep"


def test_package_member_when_cwd_is_the_package_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # the current directory itself is the package: "scream.py" inside
    # "additionals/" resolves as "additionals.scream".
    pkg = tmp_path / "additionals"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "scream.py").write_text("VALUE = 'loud'\n")
    monkeypatch.chdir(pkg)

    m = import_module("scream.py")
    assert m.VALUE == "loud"
    assert m.__name__ == "additionals.scream"


def test_import_of_init_file_returns_the_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("VALUE = 'pkg'\n")

    m = import_module("mypkg/__init__.py")
    assert m.__name__ == "mypkg"
    assert m.VALUE == "pkg"


def test_package_member_by_absolute_path(tmp_path: Path) -> None:
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "util.py").write_text("VALUE = 1\n")
    (pkg / "feature.py").write_text("from . import util\nVALUE = util.VALUE\n")

    m = import_module(str(pkg / "feature.py"))
    assert m.VALUE == 1


def test_relative_import_in_standalone_file_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # documented limitation: relative imports require a package
    monkeypatch.chdir(tmp_path)
    (tmp_path / "foo.py").write_text("from . import nosuch\n")
    with pytest.raises(ImportError):
        import_module("foo.py")


def test_import_symbol() -> None:
    assert import_symbol("kamidana._import:import_module") is import_module


def test_import_symbol_with_ns() -> None:
    assert import_symbol("import_module", ns="kamidana._import") is import_module


def test_import_symbol_missing_attribute() -> None:
    with pytest.raises(ImportError):
        import_symbol("kamidana._import:nosuch")
