import pytest
from amt.api.editable_classes import ResolvedEditable
from amt.api.editable_validators import EditableValidatorMinMaxLength, EditableValidatorSlug
from amt.schema.webform import WebFormFieldImplementationType
from fastapi.exceptions import RequestValidationError


def default_resolved_editable() -> ResolvedEditable:
    return ResolvedEditable(
        full_resource_path="/algortihm/1/this/is/a/relative/path",
        relative_resource_path="/this/is/a/relative/path",
        implementation_type=WebFormFieldImplementationType.TEXT,
    )


@pytest.mark.asyncio
async def test_editable_validator_min_max_length():
    my_validator = EditableValidatorMinMaxLength(min_length=3, max_length=10)
    resolved_editable: ResolvedEditable = default_resolved_editable()

    await my_validator.validate(in_value="this is ok", editable=resolved_editable)  # pyright: ignore[reportUnknownMemberType]

    with pytest.raises(RequestValidationError) as e:
        await my_validator.validate(in_value="this not ok because it is too long", editable=resolved_editable)  # pyright: ignore[reportUnknownMemberType]
    assert e.value.args[0][0]["loc"] == ("_this_is_a_relative_path",)
    assert e.value.args[0][0]["type"] == "string_too_long"


@pytest.mark.asyncio
async def test_editable_slug():
    my_validator = EditableValidatorSlug()

    resolved_editable: ResolvedEditable = default_resolved_editable()

    await my_validator.validate(in_value="this_is_ok", editable=resolved_editable)  # pyright: ignore[reportUnknownMemberType]

    with pytest.raises(RequestValidationError) as e:
        await my_validator.validate(in_value="t$@#@#", editable=resolved_editable)  # pyright: ignore[reportUnknownMemberType]
    assert e.value.args[0][0]["loc"] == ("_this_is_a_relative_path",)
    assert e.value.args[0][0]["type"] == "string_pattern_mismatch"
