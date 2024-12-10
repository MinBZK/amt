from amt.api.deps import LocaleJinja2Templates, custom_context_processor, permission
from amt.core.authorization import AuthorizationVerb
from tests.constants import default_fastapi_request


def test_template_permission_unauthorized():
    # given
    request = default_fastapi_request()
    templates = LocaleJinja2Templates(
        directory="tests/site/static/templates", context_processors=[custom_context_processor]
    )
    templates.env.globals.update(permission=permission)  # pyright: ignore [reportUnknownMemberType]
    templates.env.tests["permission"] = permission  # pyright: ignore [reportUnknownMemberType]

    # when
    response = templates.TemplateResponse(request, "permission_example.html.j2")

    # then
    assert b"User UnAuthorized" in response.body


def test_template_permission_authorized():
    # given
    request = default_fastapi_request()
    request.state.permissions = {
        "organization/1": [AuthorizationVerb.CREATE, AuthorizationVerb.READ, AuthorizationVerb.UPDATE]
    }
    templates = LocaleJinja2Templates(
        directory="tests/site/static/templates", context_processors=[custom_context_processor]
    )
    templates.env.globals.update(permission=permission)  # pyright: ignore [reportUnknownMemberType]
    templates.env.tests["permission"] = permission  # pyright: ignore [reportUnknownMemberType]

    # when
    response = templates.TemplateResponse(request, "permission_example.html.j2")

    # then
    assert b"User Authorized" in response.body
