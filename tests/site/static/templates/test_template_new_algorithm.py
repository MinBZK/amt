import pickle

from amt.api.deps import templates
from pytest_mock import MockFixture
from tests.constants import default_fastapi_request


def test_tempate_algorithms_new(mocker: MockFixture):
    # given
    request = default_fastapi_request()

    # TODO (Robbert): templates get to complex to test, this is a workaround for a form object
    algorithm_form = pickle.loads(  # noqa: S301
        b"\x80\x04\x95x\x01\x00\x00\x00\x00\x00\x00\x8c\x12amt.schema.webform\x94\x8c\x07WebForm\x94\x93\x94)\x81\x94}\x94(\x8c\x02id\x94\x8c\talgorithm\x94\x8c\x06legend\x94N\x8c\x08post_url\x94\x8c\x00\x94\x8c\x06fields\x94]\x94h\x00\x8c\x0cWebFormField\x94\x93\x94)\x81\x94}\x94(\x8c\x04type\x94h\x00\x8c\x10WebFormFieldType\x94\x93\x94\x8c\x06select\x94\x85\x94R\x94\x8c\x05label\x94\x8c\x0cOrganization\x94\x8c\x04name\x94\x8c\x0forganization_id\x94\x8c\x05group\x94\x8c\x011\x94\x8c\x0bplaceholder\x94N\x8c\rdefault_value\x94h\t\x8c\x07options\x94]\x94h\x00\x8c\rWebFormOption\x94\x93\x94)\x81\x94}\x94(\x8c\x05value\x94h\t\x8c\rdisplay_value\x94\x8c\x13Select organization\x94uba\x8c\nattributes\x94N\x8c\x0bdescription\x94Nubaub."  # noqa: E501
    )

    context = {
        "algorithm": "",
        "instruments": "",
        "ai_act_profile": {"category": ["option"]},
        "form": algorithm_form,
    }

    # when
    response = templates.TemplateResponse(request, "algorithms/new.html.j2", context)

    # then
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"
    assert b"Create Algorithm" in response.body
