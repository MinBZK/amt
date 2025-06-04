from dataclasses import dataclass
from typing import Any  # pyright: ignore[reportUnusedImport]

import pytest
from amt.api.update_utils import extract_number_and_string, set_path


@dataclass
class TestObject:
    name: str = ""
    nested: dict[str, Any] | None = None
    items: list[str] | None = None

    def __post_init__(self) -> None:
        if self.nested is None:
            self.nested = {}


def test_extract_number_and_string() -> None:
    # given
    test_cases: list[tuple[str, tuple[str, int | None]]] = [
        ("name", ("name", None)),
        ("name[0]", ("name", 0)),
        ("name[123]", ("name", 123)),
        ("complex[10]", ("complex", 10)),
        ("nested.deeply[5]", ("nested.deeply", 5)),
        ("[5]", ("", 5)),
    ]

    # when/then
    for input_string, expected in test_cases:
        result = extract_number_and_string(input_string)
        assert result == expected


def test_set_path_dict_simple() -> None:
    # given
    obj: dict[str, Any] = {}
    path = "name"
    value = "test value"

    # when
    set_path(obj, path, value)

    # then
    assert obj["name"] == "test value"


def test_set_path_dict_nested() -> None:
    # given
    obj: dict[str, Any] = {}
    path = "nested/deeply/value"
    value = "nested value"

    # when
    set_path(obj, path, value)

    # then
    assert obj["nested"]["deeply"]["value"] == "nested value"


def test_set_path_dict_list_index() -> None:
    # given
    obj: dict[str, Any] = {"items": [{"id": 1}, {"id": 2}, {"id": 3}]}
    path = "items[1]/name"
    value = "item name"

    # when
    set_path(obj, path, value)

    # then
    assert obj["items"][1]["name"] == "item name"


def test_set_path_object_simple() -> None:
    # given
    obj = TestObject()
    path = "name"
    value = "test value"

    # when
    set_path(obj, path, value)

    # then
    assert obj.name == "test value"


def test_set_path_object_nested() -> None:
    # given
    nested_obj = TestObject()
    obj = TestObject(nested=nested_obj)  # pyright: ignore[reportGeneralTypeIssues, reportArgumentType]
    path = "nested/name"
    value = "nested name"

    # when
    set_path(obj, path, value)

    # then
    assert obj.nested.name == "nested name"  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportOptionalMemberAccess]


def test_set_path_object_create_nested() -> None:
    # given
    obj = TestObject()
    path = "nested/deeply/name"
    value = "deeply nested"

    # when
    set_path(obj, path, value)

    # then
    assert obj.nested["deeply"]["name"] == "deeply nested"  # pyright: ignore[reportOptionalSubscript]


def test_set_path_object_list() -> None:
    # given
    obj = TestObject(items=["a", "b", "c"])
    path = "items[1]"
    value = "updated"

    # when
    set_path(obj, path, value)

    # then
    assert obj.items is not None
    assert obj.items[1] == "updated"


def test_set_path_empty_path() -> None:
    # given
    obj: dict[str, Any] = {}
    path = ""
    value = "test"

    # when/then
    with pytest.raises(ValueError, match="Path cannot be empty"):
        set_path(obj, path, value)
