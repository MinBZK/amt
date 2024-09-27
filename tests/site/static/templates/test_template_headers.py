from amt.api.deps import templates
from tests.constants import default_fastapi_request


def test_template_caching():
    # given
    request = default_fastapi_request()

    # when
    response = templates.TemplateResponse(
        request, "errors/Exception.html.j2", headers={"Content-Language": "This is a test"}
    )

    # then
    assert response.headers["Content-Language"] == "This is a test"
