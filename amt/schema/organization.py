from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator


class OrganizationBase(BaseModel):
    name: str = Field(min_length=3, max_length=64)


class OrganizationSlug(BaseModel):
    slug: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9-_]*{3,64}$")


class OrganizationNew(OrganizationBase, OrganizationSlug):
    user_ids: list[str] | str

    @field_validator("user_ids")
    def ensure_list(cls, v: list[str] | str) -> list[str]:
        return v if isinstance(v, list) else [v]
