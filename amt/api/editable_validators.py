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
    async def validate(self, in_value: Any, relative_resource_path: str) -> None:  # noqa: ANN401
        pass


class EditableValidatorMinMaxLength(EditableValidator):
    def __init__(self, min_length: int, max_length: int) -> None:
        class FieldValidator(BaseModel):
            value: str = Field(min_length=min_length, max_length=max_length)

        self.field_validator: type[FieldValidator] = FieldValidator

    async def validate(self, in_value: str, relative_resource_path: str) -> None:
        try:
            self.field_validator(value=in_value)
        except ValidationError as e:
            errors = e.errors()
            errors[0]["loc"] = (relative_resource_path.replace("/", "_"),)
            raise RequestValidationError(errors) from e


class EditableValidatorSlug(EditableValidator):
    async def validate(self, in_value: str, relative_resource_path: str) -> None:
        try:
            organization_slug: OrganizationSlug = OrganizationSlug(slug=in_value)
            OrganizationSlug.model_validate(organization_slug)
        except ValidationError as e:
            errors = e.errors()
            errors[0]["loc"] = (relative_resource_path.replace("/", "_"),)
            raise RequestValidationError(errors) from e
