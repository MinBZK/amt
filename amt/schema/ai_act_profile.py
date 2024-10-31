from pydantic import field_validator

from amt.schema.shared import BaseModel


class AiActProfile(BaseModel):
    type: str | None
    open_source: str | None
    publication_category: str | None
    systemic_risk: str | None
    transparency_obligations: str | None
    role: list[str] | str | None

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
