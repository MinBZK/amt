from pydantic import BaseModel


class AiActProfile(BaseModel):
    type: str | None
    open_source: str | None
    publication_category: str | None
    systemic_risk: str | None
    transparency_obligations: str | None
    role: str | None
