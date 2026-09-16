from pathlib import Path

import pytest

pydantic = pytest.importorskip("pydantic")

from kamidana._import import import_symbol
from kamidana.loader import TemplateLoader


ROOT = Path(__file__).resolve().parents[2]
DRIVER_PATH = ROOT / "examples" / "validation" / "validating_driver.py"


def make_driver(data):
    driver_cls = import_symbol(
        "{}:ValidatingDriver".format(DRIVER_PATH), cwd=True
    )
    loader = TemplateLoader([str(data)], [], [])
    return driver_cls(loader, "raw")


def test_invalid_data_does_not_write_output(tmp_path):
    driver = make_driver(ROOT / "examples" / "validation" / "data.ng.yaml")
    dst = tmp_path / "output.txt"

    with pytest.raises(pydantic.ValidationError) as exc_info:
        driver.run(
            str(ROOT / "examples" / "validation" / "template.j2"),
            str(dst),
        )

    assert len(exc_info.value.errors()) == 2
    assert not dst.exists()


def test_valid_data_renders_defaults_and_coerced_values(tmp_path):
    driver = make_driver(ROOT / "examples" / "validation" / "data.ok.yaml")
    dst = tmp_path / "output.txt"

    driver.run(
        str(ROOT / "examples" / "validation" / "template.j2"),
        str(dst),
    )

    assert dst.read_text() == "hello, foo!\nlistening on port 8081\n"
