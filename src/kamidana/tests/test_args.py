from __future__ import annotations

import pytest

from kamidana.commands._args import make_common_parser


def test_data_options_preserve_argv_order() -> None:
    # -d and --data-json are the same tier: they land in one list in
    # command-line order, later entries winning the merge.
    parser = make_common_parser()
    args = parser.parse_args(
        ["-d", "a.yaml", "--data-json", '{"x": 1}', "-d", "b.yaml"]
    )
    assert args.data == [
        ("file", "a.yaml"),
        ("json", {"x": 1}),
        ("file", "b.yaml"),
    ]


def test_data_json_before_file() -> None:
    parser = make_common_parser()
    args = parser.parse_args(["--data-json", '{"x": 1}', "-d", "b.yaml"])
    assert args.data == [("json", {"x": 1}), ("file", "b.yaml")]


def test_data_json_rejects_non_object() -> None:
    parser = make_common_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--data-json", "[1, 2]"])


def test_data_json_rejects_invalid_json() -> None:
    parser = make_common_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--data-json", "{oops"])
