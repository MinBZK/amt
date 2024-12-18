from pydantic import BaseModel, Field
from pydantic.functional_validators import field_validator


class AlgorithmBase(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    lifecycle: str = Field()


class AlgorithmNew(AlgorithmBase):
    instruments: list[str] | str = []
    type: str | None = Field(default=None)
    open_source: str | None = Field(default=None)
    risk_group: str | None = Field(default=None)
    conformity_assessment_body: str | None = Field(default=None)
    systemic_risk: str | None = Field(default=None)
    transparency_obligations: str | None = Field(default=None)
    role: list[str] | str = []
    template_id: str | None = Field(default=None)
    organization_id: int = Field()

    @field_validator("organization_id", mode="before")
    @classmethod
    def ensure_required(cls, v: int | str) -> int:
        if isinstance(v, str) and v == "":  # this is always a string
            # TODO (Robbert): the error message from pydantic becomes 'Value error,
            #  missing' which is why a custom message will be applied
            raise ValueError("missing")
        else:
            return int(v)

    @field_validator("instruments", "role")
    @classmethod
    def ensure_list(cls, v: list[str] | str) -> list[str]:
        return v if isinstance(v, list) else [v]
