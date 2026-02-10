from typing import Any, cast

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from pydantic import Field, ValidationError

from amt.api.editable_classes import EditableValidator, EditModes, ResolvedEditable
from amt.schema.organization import OrganizationSlug
from amt.schema.shared import BaseModel
from amt.services.services_provider import ServicesProvider


class EditableValidatorMustHaveItems(EditableValidator):
    async def validate(
        self,
        request: Request,
        editable: ResolvedEditable,
        editable_context: dict[str, str | dict[str, str]],
        edit_mode: EditModes,
        services_provider: ServicesProvider,
    ) -> None:
        in_value = self.get_new_value(editable, editable_context)
        if not isinstance(in_value, list) or len(cast(list[Any], in_value)) == 0:
            errors = [{"loc": [editable.safe_html_path()], "type": "missing"}]
            raise RequestValidationError(errors)


class EditableValidatorMinMaxLength(EditableValidator):
    def __init__(self, min_length: int, max_length: int) -> None:
        class FieldValidator(BaseModel):
            value: str = Field(min_length=min_length, max_length=max_length)

        self.field_validator: type[FieldValidator] = FieldValidator

    async def validate(
        self,
        request: Request,
        editable: ResolvedEditable,
        editable_context: dict[str, str | dict[str, str]],
        edit_mode: EditModes,
        services_provider: ServicesProvider,
    ) -> None:
        in_value = self.get_new_value(editable, editable_context)
        try:
            self.field_validator(value=in_value)
        except ValidationError as e:
            errors = e.errors()
            errors[0]["loc"] = (editable.safe_html_path(),)  # pyright: ignore[reportUnknownMemberType]
            raise RequestValidationError(errors) from e


class EditableValidatorSlug(EditableValidator):
    async def validate(
        self,
        request: Request,
        editable: ResolvedEditable,
        editable_context: dict[str, str | dict[str, str]],
        edit_mode: EditModes,
        services_provider: ServicesProvider,
    ) -> None:
        in_value = self.get_new_value(editable, editable_context)
        try:
            organization_slug: OrganizationSlug = OrganizationSlug(slug=in_value)
            OrganizationSlug.model_validate(organization_slug)
        except ValidationError as e:
            errors = e.errors()
            errors[0]["loc"] = (editable.safe_html_path(),)  # pyright: ignore[reportUnknownMemberType]
            raise RequestValidationError(errors) from e


class EditableValidatorRequiredField(EditableValidator):
    async def validate(
        self,
        request: Request,
        editable: ResolvedEditable,
        editable_context: dict[str, str | dict[str, str]],
        edit_mode: EditModes,
        services_provider: ServicesProvider,
    ) -> None:
        in_value = self.get_new_value(editable, editable_context)
        if in_value is None or in_value == "":
            errors = [{"loc": [editable.safe_html_path()], "type": "missing"}]
            raise RequestValidationError(errors)
