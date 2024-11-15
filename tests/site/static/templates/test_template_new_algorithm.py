from amt.api.deps import templates
from tests.constants import default_fastapi_request


def test_tempate_algorithms_new():
    # given
    request = default_fastapi_request()
    context = {"algorithm": "", "instruments": "", "ai_act_profile": {"category": ["option"]}}

    # when
    response = templates.TemplateResponse(request, "algorithms/new.html.j2", context)

    # then
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"
    assert b"Create Algorithm" in response.body
