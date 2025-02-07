from abc import ABC, abstractmethod
from typing import Any

from fastapi.exceptions import RequestValidationError
from pydantic import Field, ValidationError

from amt.schema.organization import OrganizationSlug
from amt.schema.shared import BaseModel


class EditableValidator(ABC):
    """
    Validators are used to validate (input) data for logical rules, like length and allowed characters.
    """

    @abstractmethod
    async def validate(self, in_value: Any, editable: "ResolvedEditable") -> None:  # noqa: ANN401, F821 # pyright: ignore[reportUndefinedVariable, reportUnknownParameterType]
        pass


class EditableValidatorMinMaxLength(EditableValidator):
    def __init__(self, min_length: int, max_length: int) -> None:
        class FieldValidator(BaseModel):
            value: str = Field(min_length=min_length, max_length=max_length)

        self.field_validator: type[FieldValidator] = FieldValidator

    async def validate(self, in_value: str, editable: "ResolvedEditable") -> None:  # noqa: F821 # pyright: ignore[reportUndefinedVariable, reportUnknownParameterType]
        try:
            self.field_validator(value=in_value)
        except ValidationError as e:
            errors = e.errors()
            errors[0]["loc"] = (editable.safe_html_path(),)  # pyright: ignore[reportUnknownMemberType]
            raise RequestValidationError(errors) from e


class EditableValidatorSlug(EditableValidator):
    async def validate(self, in_value: str, editable: "ResolvedEditable") -> None:  # noqa: F821 # pyright: ignore[reportUndefinedVariable, reportUnknownParameterType]
        try:
            organization_slug: OrganizationSlug = OrganizationSlug(slug=in_value)
            OrganizationSlug.model_validate(organization_slug)
        except ValidationError as e:
            errors = e.errors()
            errors[0]["loc"] = (editable.safe_html_path(),)  # pyright: ignore[reportUnknownMemberType]
            raise RequestValidationError(errors) from e
