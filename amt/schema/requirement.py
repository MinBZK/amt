from enum import Enum

from pydantic import Field

from amt.schema.shared import BaseModel


class TypeEnum(Enum):
    AI_systeem = "AI-systeem"
    AI_systeem_voor_algemene_doeleinden = "AI-systeem voor algemene doeleinden"
    AI_model_voor_algemene_doeleinden = "AI-model voor algemene doeleinden"
    geen_algoritme = "geen algoritme"
    impactvol_algoritme = "impactvol algoritme"
    niet_impactvol_algoritme = "niet-impactvol algoritme"


class OpenSourceEnum(Enum):
    open_source = "open-source"
    geen_open_source = "geen open-source"


class RiskGroupEnum(Enum):
    geen_hoog_risico_AI = "geen hoog-risico AI"
    hoog_risico_AI = "hoog-risico AI"
    verboden_AI = "verboden AI"
    uitzondering_van_toepassing = "uitzondering van toepassing"


class SystemicRiskEnum(Enum):
    systeemrisico = "systeemrisico"
    geen_systeemrisico = "geen systeemrisico"


class TransparencyObligationEnum(Enum):
    transparantieverplichting = "transparantieverplichting"
    geen_transparantieverplichting = "geen transparantieverplichting"


class ConformityAssessmentBodyEnum(Enum):
    beoordeling_door_derde_partij = "beoordeling door derde partij"


class RoleEnum(Enum):
    aanbieder = "aanbieder"
    gebruiksverantwoordelijke = "gebruiksverantwoordelijke"
    importeur = "importeur"
    distributeur = "distributeur"


class RequirementAiActProfile(BaseModel):
    type: list[TypeEnum]
    open_source: list[OpenSourceEnum]
    risk_group: list[RiskGroupEnum]
    systemic_risk: list[SystemicRiskEnum]
    transparency_obligations: list[TransparencyObligationEnum]
    conformity_assessment_body: list[ConformityAssessmentBodyEnum]
    role: list[RoleEnum]


class RequirementBase(BaseModel):
    urn: str


class RequirementTask(RequirementBase):
    state: str = Field(default="")
    version: str


class Requirement(RequirementBase):
    name: str
    description: str
    schema_version: str
    links: list[str] = Field(default=[])
    ai_act_profile: list[RequirementAiActProfile]
    always_applicable: int = Field(
        ...,
        description="1 if requirements applies to every system, 0 if only for specific systems",
    )
