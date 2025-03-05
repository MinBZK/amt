from dataclasses import dataclass  # noqa: I001

from amt.api.deps import custom_context_processor, hasattr_jinja, permission, instance, equal_or_includes
from amt.core.authorization import AuthorizationVerb
from amt.schema.shared import IterMixin

from tests.constants import default_fastapi_request
import pytest

example_permissions = {
    "organization/1": [AuthorizationVerb.CREATE, AuthorizationVerb.READ, AuthorizationVerb.UPDATE],
    "organization/1/algorithm": [
        AuthorizationVerb.LIST,
        AuthorizationVerb.CREATE,
        AuthorizationVerb.UPDATE,
        AuthorizationVerb.DELETE,
    ],
    "organization/1/member": [
        AuthorizationVerb.LIST,
        AuthorizationVerb.CREATE,
        AuthorizationVerb.UPDATE,
        AuthorizationVerb.DELETE,
    ],
    "algoritme/1": [AuthorizationVerb.CREATE, AuthorizationVerb.READ, AuthorizationVerb.DELETE],
    "algoritme/1/systemcard": [AuthorizationVerb.READ, AuthorizationVerb.CREATE, AuthorizationVerb.UPDATE],
    "algoritme/1/user": [
        AuthorizationVerb.CREATE,
        AuthorizationVerb.READ,
        AuthorizationVerb.UPDATE,
        AuthorizationVerb.DELETE,
    ],
}


def test_custom_context_processor():
    result = custom_context_processor(default_fastapi_request())
    assert result is not None
    assert result["version"] == "0.1.0"
    assert result["available_translations"] == ["en", "nl"]
    assert result["language"] == "en"
    assert result["translations"] is None


def test_permissions_false():
    result = permission("organization/1", AuthorizationVerb.LIST, example_permissions)

    assert result is False


def test_permissions_true():
    result = permission("organization/1", AuthorizationVerb.READ, example_permissions)

    assert result is True


def test_permissions_none_existing_resource():
    result = permission("badfadfb/1", AuthorizationVerb.READ, example_permissions)

    assert result is False


def test_hasattr_jinja():
    @dataclass
    class Test2:
        field3: str | None = None

    @dataclass
    class Test1:
        field1: str | None = None
        field2: Test2 | None = None

    my_class = Test1(field1="test", field2=Test2(field3=None))
    assert hasattr_jinja(my_class, "field2.field3") is False

    my_class_2 = Test1(field1="test", field2=Test2(field3="Hello"))
    assert hasattr_jinja(my_class_2, "field2.field3") is True


def test_instance():
    assert instance("str", "str")
    assert instance(["1", "2"], "list")
    assert instance({"k": "v"}, "dict")
    assert instance(IterMixin(), "IterMixin")
    with pytest.raises(TypeError):
        instance("str", "unknown")


def test_equal_or_includes():
    assert equal_or_includes("abc", "abc")
    assert equal_or_includes("abc", ["abc", "def"])
    assert False is equal_or_includes("abcd", ["abc", "def"])
    assert False is equal_or_includes("abcd", IterMixin())  # pyright: ignore[reportArgumentType]
