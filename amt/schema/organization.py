from pydantic import BaseModel, Field


class OrganizationBase(BaseModel):
    name: str = Field(min_length=3, max_length=64)


class OrganizationSlug(BaseModel):
    slug: str = Field(min_length=3, max_length=64, pattern=r"^[a-z0-9-_]*{3,64}$")


class OrganizationNew(OrganizationBase, OrganizationSlug):
    pass
