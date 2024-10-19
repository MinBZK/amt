from collections.abc import Callable
from enum import Enum
from unittest.mock import Mock

import pytest
from amt.api.deps import (
    custom_context_processor,
    get_nested,
    is_nested_enum,
    nested_enum,
    nested_enum_value,
    nested_value,
)
from amt.api.localizable import LocalizableEnum
from amt.core.config import VERSION
from amt.core.internationalization import supported_translations
from amt.schema.localized_value_item import LocalizedValueItem
from fastapi import Request


def test_custom_context_processor():
    request: Request = Mock()
    request.cookies.get.return_value = "nl"
    request.headers.get.return_value = "nl"
    result = custom_context_processor(request)
    assert list(result.keys()) == [
        "version",
        "available_translations",
        "language",
        "translations",
        "main_menu_items",
        "user",
    ]
    assert result["version"] == VERSION
    assert result["available_translations"] == list(supported_translations)
    assert result["language"] == "nl"


# Mock classes and functions for testing
class MockEnum(Enum):
    A = 1
    B = 2


class MockLocalizableEnum(LocalizableEnum):
    X = "X"
    Y = "Y"

    @classmethod
    def get_display_values(
        cls: type["MockLocalizableEnum"], _: Callable[[str], str]
    ) -> dict["MockLocalizableEnum", str]:
        return {cls.X: _("x"), cls.Y: _("y")}


def test_get_nested():
    obj = {"a": {"b": {"c": 1}}}
    assert get_nested(obj, "a.b.c") == 1
    assert get_nested(obj, "a.b.d") is None

    class NestedObj:
        def __init__(self) -> None:
            self.x = {"y": 2}

    nested_obj = NestedObj()
    assert get_nested(nested_obj, "x.y") == 2
    assert get_nested(nested_obj, "x.z") is None


# Test nested_value function
def test_nested_value():
    obj = {"a": {"b": MockEnum.A}}
    assert nested_value(obj, "a.b") == 1

    obj2 = {"a": {"b": "not enum"}}
    assert nested_value(obj2, "a.b") == "not enum"


# Test is_nested_enum function
def test_is_nested_enum():
    obj = {"a": {"b": MockEnum.A}}
    assert is_nested_enum(obj, "a.b") is True

    obj2 = {"a": {"b": "not enum"}}
    assert is_nested_enum(obj2, "a.b") is False


# Test nested_enum function
def test_nested_enum():
    class TestObj:
        attr = MockLocalizableEnum.X

    obj = TestObj()
    result = nested_enum(obj, "attr", "en")
    assert len(result) == 2
    assert all(isinstance(item, LocalizedValueItem) for item in result)
    assert result[0].value == "X"
    assert result[0].display_value == "x"

    obj2 = {"a": "not enum"}
    assert nested_enum(obj2, "a", "en") == []


# Test nested_enum_value function
def test_nested_enum_value():
    class TestObj:
        attr = MockLocalizableEnum.X

    obj = TestObj()
    e = nested_enum_value(obj, "attr", "en")
    assert e.display_value == "x"

    with pytest.raises(AttributeError):
        nested_enum_value({"a": "not enum"}, "a", "en")
