import pytest
from amt.api.editable_validators import EditableValidatorMinMaxLength, EditableValidatorSlug
from fastapi.exceptions import RequestValidationError


@pytest.mark.asyncio
async def test_editable_validator_min_max_length():
    my_validator = EditableValidatorMinMaxLength(min_length=3, max_length=10)

    await my_validator.validate(in_value="this is ok", relative_resource_path="/this/is/a/relative/path")

    with pytest.raises(RequestValidationError) as e:
        await my_validator.validate(
            in_value="this not ok because it is too long", relative_resource_path="/this/is/a/relative/path"
        )
    assert e.value.args[0][0]["loc"] == ("_this_is_a_relative_path",)
    assert e.value.args[0][0]["type"] == "string_too_long"


@pytest.mark.asyncio
async def test_editable_slug():
    my_validator = EditableValidatorSlug()

    await my_validator.validate(in_value="this_is_ok", relative_resource_path="/this/is/a/relative/path")

    with pytest.raises(RequestValidationError) as e:
        await my_validator.validate(in_value="t$@#@#", relative_resource_path="/this/is/a/relative/path")
    assert e.value.args[0][0]["loc"] == ("_this_is_a_relative_path",)
    assert e.value.args[0][0]["type"] == "string_pattern_mismatch"
