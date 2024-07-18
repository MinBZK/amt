from tad.api.deps import templates
from tests.constants import default_fastapi_request


def test_template_redirect():
    # given
    request = default_fastapi_request()

    # when
    response = templates.TemplateResponse(request, "redirect.html.j2")

    # then
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"
    assert response.body == b""
