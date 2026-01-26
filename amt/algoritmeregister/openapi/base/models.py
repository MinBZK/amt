"""
Pydantic models for the Algoritmeregister Base API.

These models are manually created for endpoints not included in the versioned API spec.
See openapi/base/specs/openapi.json for the reference specification.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class Role(str, Enum):
    DISABLED = "disabled"
    ALL_GROUPS = "all_groups"
    ADMIN = "admin"
    ORGDETAIL = "orgdetail"
    ICTU = "ictu"
    ROLE_1 = "role_1"
    ROLE_2 = "role_2"


class OrgType(str, Enum):
    ADVIESCOLLEGE = "adviescollege"
    AGENTSCHAP = "agentschap"
    BRANDWEER = "brandweer"
    CARIBISCH_OPENBAAR_LICHAAM = "caribisch_openbaar_lichaam"
    GEMEENTE = "gemeente"
    GRENSOVERSCHRIJDEND_REGIONAAL_SAMENWERKINGSORGAAN = "grensoverschrijdend_regionaal_samenwerkingsorgaan"
    HOOG_COLLEGE_VAN_STAAT = "hoog_college_van_staat"
    INTERDEPARTEMENTALE_COMMISSIE = "interdepartementale_commissie"
    KABINET_VAN_DE_KONING = "kabinet_van_de_koning"
    KOEPELORGANISATIE = "koepelorganisatie"
    MINISTERIE = "ministerie"
    OMGEVINGSDIENST = "omgevingsdienst"
    OPENBAAR_LICHAAM_VOOR_BEROEP_EN_BEDRIJF = "openbaar_lichaam_voor_beroep_en_bedrijf"
    ORGANISATIE_MET_OVERHEIDSBEMOEIENIS = "organisatie_met_overheidsbemoeienis"
    ORGANISATIEONDERDEEL = "organisatieonderdeel"
    POLITIE = "politie"
    PROVINCIE = "provincie"
    REGIONAAL_SAMENWERKINGSVERBAND = "regionaal_samenwerkingsverband"
    RECHTSPRAAK = "rechtspraak"
    REGIONAAL_SAMENWERKINGSORGAAN = "regionaal_samenwerkingsorgaan"
    WATERSCHAP = "waterschap"
    ZELFSTANDIG_BESTUURSORGAAN = "zelfstandig_bestuursorgaan"
    OVERIG = "overig"
    VEILIGHEIDSREGIO = "veiligheidsregio"
    INSPECTIE = "inspectie"


class Flow(str, Enum):
    ICTU_LAST = "ictu_last"
    SELF_PUBLISH_TWO = "self_publish_two"


class OrganisationConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    id: int
    name: str
    code: str
    org_id: str
    type: OrgType
    flow: Flow
    show_page: bool


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    id: str
    username: str
    first_name: str
    last_name: str
    roles: list[Role]
    organisations: list[OrganisationConfig]


class GetOrganisationsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    organisations: list[OrganisationConfig]
    count: int
