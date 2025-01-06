from amt.api.deps import custom_context_processor, permission
from amt.core.authorization import AuthorizationVerb

from tests.constants import default_fastapi_request

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
