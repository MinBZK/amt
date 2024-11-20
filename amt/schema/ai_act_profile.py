from pydantic import Field, field_validator

from amt.schema.shared import BaseModel


class AiActProfile(BaseModel):
    type: str | None = Field(default=None)
    open_source: str | None = Field(default=None)
    publication_category: str | None = Field(default=None)
    systemic_risk: str | None = Field(default=None)
    transparency_obligations: str | None = Field(default=None)
    role: list[str] | str | None = Field(default=None)

    @field_validator("role")
    def compute_role(cls, v: list[str] | None) -> str | None:
        if v is None:
            return None

        if isinstance(v, str):
            return v

        if len(v) <= 2:
            if len(v) == 0:
                return None
            elif len(v) == 1:
                return v[0]
            else:
                return f"{v[0]} + {v[1]}"
        else:
            raise ValueError("There can only be two roles")
