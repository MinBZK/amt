from datetime import date, datetime
from enum import Enum

from pydantic import Field

from amt.schema.ai_act_profile import AiActProfile
from amt.schema.assessment_card import AssessmentCard
from amt.schema.instrument import InstrumentBase
from amt.schema.measure import MeasureTask
from amt.schema.model_card import ModelCardSchema
from amt.schema.requirement import RequirementTask
from amt.schema.shared import BaseModel


class Provenance(BaseModel):
    git_commit_hash: str | None = Field(
        None,
        description="Git commit hash of the commit which contains the transformation file used to create this card",
    )
    timestamp: datetime | None = Field(
        None,
        description="A timestamp of the date, time and timezone of generation of this System Card in ISO 8601 format",
    )
    uri: str | None = Field(None, description="URI to the tool that was used to perform the transformations")
    author: str | None = Field(None, description="Name of person that initiated the transformations")


class Type(Enum):
    AI_systeem = "AI-systeem"
    AI_systeem_voor_algemene_doeleinden = "AI-systeem voor algemene doeleinden"
    AI_model_voor_algemene_doeleinden = "AI-model voor algemene doeleinden"
    geen_algoritme = "geen algoritme"


class OpenSource(Enum):
    open_source = "open-source"
    geen_open_source = "geen open-source"


class PublicationCategory(Enum):
    impactvol_algoritme = "impactvol algoritme"
    niet_impactvol_algoritme = "niet-impactvol algoritme"
    hoog_risico_AI = "hoog-risico AI"
    geen_hoog_risico_AI = "geen hoog-risico AI"
    verboden_AI = "verboden AI"
    uitzondering_van_toepassing = "uitzondering van toepassing"


class SystemicRisk(Enum):
    systeemrisico = "systeemrisico"
    geen_systeemrisico = "geen systeemrisico"


class TransparencyObligations(Enum):
    transparantieverplichtingen = "transparantieverplichtingen"
    geen_transparantieverplichtingen = "geen transparantieverplichtingen"


class Role(Enum):
    aanbieder = "aanbieder"
    gebruiksverantwoordelijke = "gebruiksverantwoordelijke"
    aanbieder___gebruiksverantwoordelijke = "aanbieder + gebruiksverantwoordelijke"


class DecisionTree(BaseModel):
    version: str | None = Field(None, description="The version of the decision tree")


class Label(BaseModel):
    name: str | None = Field(None, description="Name of the label")
    value: str | None = Field(None, description="Value of the label")


class LegalBaseItem(BaseModel):
    name: str | None = Field(None, description="Name of the law")
    link: str | None = Field(None, description="URI pointing towards the contents of the law")


class ExternalProvider(BaseModel):
    name: str | None = Field(None, description="Name of the external provider")
    version: str | None = Field(
        None,
        description="Version of the external provider reflecting its relation to previous versions",
    )


class UserInterfaceItem(BaseModel):
    description: str | None = Field(None, description="A description of the provided user interface")
    link: str | None = Field(None, description="A link to the user interface can be included")
    snapshot: str | None = Field(
        None,
        description="A snapshot/screenshot of the user interface can be included with the use of a hyperlink",
    )


class Reference(BaseModel):
    name: str | None = Field(default=None)
    link: str | None = Field(default=None)


class Owner(BaseModel):
    oin: str | None = Field(None, description="If applicable the Organisatie-identificatienummer (OIN)")
    organization: str | None = Field(
        None,
        description="Name of the organization that owns the model. If ion is NOT provided this field is REQUIRED",
    )
    name: str | None = Field(None, description="Name of a contact person within the organization")
    email: str | None = Field(None, description="Email address of the contact person or organization")
    role: str | None = Field(
        None,
        description="Role of the contact person. This field should only be set when the name field is set",
    )


class SystemCard(BaseModel):
    version: str | None = Field(description="The version of the schema used", default="0.0.0")
    provenance: Provenance | None = None
    name: str | None = Field(None, description="Name used to describe the system")
    instruments: list[InstrumentBase] = Field(default_factory=list[InstrumentBase])
    upl: str | None = Field(
        None,
        description="If this algorithm is part of a product offered by the Dutch Government,"
        "it should contain a URI from the Uniform Product List",
    )
    owners: list[Owner] = Field(default_factory=list[Owner])
    description: str | None = Field(None, description="A short description of the system")
    ai_act_profile: AiActProfile | None = None
    labels: list[Label] | None = Field(
        default_factory=list[Label], description="Labels to store meta information about the system"
    )
    status: str | None = Field(None, description="Status of the system")
    begin_date: date | None = Field(
        None,
        description="The first date the system was used, in ISO 8601 format, i.e. YYYY-MM-DD."
        "Left out if not yet in use.",
    )
    end_date: date | None = Field(
        None,
        description="The last date the system was used, in ISO 8601 format, i.e. YYYY-MM-DD. Left out if still in use.",
    )
    goal_and_impact: str | None = Field(
        None,
        description="The purpose of the system and the impact it has on citizens and companies",
    )
    considerations: str | None = Field(None, description="The pro's and con's of using the system")
    risk_management: str | None = Field(None, description="Description of the risks associated with the system")
    human_intervention: str | None = Field(
        None,
        description="A description to want extend there is human involvement in the system",
    )
    legal_base: list[LegalBaseItem] | None = Field(
        None, description="Relevant laws for the process the system is embedded in"
    )
    used_data: str | None = Field(None, description="An overview of the data that is used in the system")
    technical_design: str | None = Field(None, description="Description on how the system works")
    external_providers: list[str] | None = Field(None, description="Information on external providers")
    interaction_details: list[str] | None = Field(
        None,
        description="How the AI system interacts with hardware or software, including other AI systems",
    )
    version_requirements: list[str] | None = Field(
        None,
        description="The versions of the relevant software or firmware,and any requirements related to version updates",
    )
    deployment_variants: list[str] | None = Field(
        None,
        description="All the forms in which the AI system is placed on the market or put into service,"
        "such as software packages embedded into hardware, downloads, or APIs",
    )
    hardware_requirements: list[str] | None = Field(
        None,
        description="Description of the hardware on which the AI system must be run",
    )
    product_markings: list[str] | None = Field(
        None,
        description="If the AI system is a component of products, photos, or illustrations, "
        "the external features, markings, and internal layout of those products",
    )
    user_interface: list[UserInterfaceItem] | None = Field(
        None,
        description="Information on the user interface provided to the user responsible for its operation",
    )

    schema_version: str = Field(default="0.1a10")
    requirements: list[RequirementTask] = Field(default=[])
    measures: list[MeasureTask] = Field(default=[])
    assessments: list[AssessmentCard] = Field(default=[])
    references: list[Reference] = Field(default=[])
    models: list[ModelCardSchema] = Field(default=[])
