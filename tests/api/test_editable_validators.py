import pytest
from amt.api.editable_classes import EditModes, ResolvedEditable
from amt.api.editable_validators import EditableValidatorMinMaxLength, EditableValidatorSlug
from amt.schema.webform_classes import WebFormFieldImplementationType
from amt.services.services_provider import ServicesProvider
from fastapi.exceptions import RequestValidationError
from pytest_mock import MockerFixture

from tests.constants import default_fastapi_request


def default_resolved_editable() -> ResolvedEditable:
    return ResolvedEditable(
        full_resource_path="/algortihm/1/name",
        relative_resource_path="name",
        implementation_type=WebFormFieldImplementationType.TEXT,
    )


@pytest.mark.asyncio
async def test_editable_validator_min_max_length(mocker: MockerFixture):
    my_validator = EditableValidatorMinMaxLength(min_length=3, max_length=10)
    resolved_editable: ResolvedEditable = default_resolved_editable()
    editable_context: dict[str, str | dict[str, str]] = {
        "new_values": {"name": "this is ok"},
    }
    services_provider = mocker.Mock(spec=ServicesProvider)

    await my_validator.validate(
        request=default_fastapi_request(),
        editable=resolved_editable,
        editable_context=editable_context,
        edit_mode=EditModes.EDIT,
        services_provider=services_provider,
    )  # pyright: ignore[reportUnknownMemberType]

    editable_context: dict[str, str | dict[str, str]] = {
        "new_values": {"name": "this not ok because it is too long"},
    }
    with pytest.raises(RequestValidationError) as e:
        await my_validator.validate(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context=editable_context,
            edit_mode=EditModes.EDIT,
            services_provider=services_provider,
        )  # pyright: ignore[reportUnknownMemberType]
    assert e.value.args[0][0]["loc"] == ("name",)
    assert e.value.args[0][0]["type"] == "string_too_long"


@pytest.mark.asyncio
async def test_editable_slug(mocker: MockerFixture):
    my_validator = EditableValidatorSlug()

    resolved_editable: ResolvedEditable = default_resolved_editable()
    services_provider = mocker.Mock(spec=ServicesProvider)

    editable_context: dict[str, str | dict[str, str]] = {
        "new_values": {"name": "this_is_ok"},
    }

    await my_validator.validate(
        request=default_fastapi_request(),
        editable=resolved_editable,
        editable_context=editable_context,
        edit_mode=EditModes.EDIT,
        services_provider=services_provider,
    )  # pyright: ignore[reportUnknownMemberType]

    editable_context: dict[str, str | dict[str, str]] = {
        "new_values": {"name": "t$@#@#"},
    }
    with pytest.raises(RequestValidationError) as e:
        await my_validator.validate(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context=editable_context,
            edit_mode=EditModes.EDIT,
            services_provider=services_provider,
        )  # pyright: ignore[reportUnknownMemberType]
    assert e.value.args[0][0]["loc"] == ("name",)
    assert e.value.args[0][0]["type"] == "string_pattern_mismatch"
