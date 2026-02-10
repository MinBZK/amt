import json
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus
from uuid import UUID

from amt.api.lifecycles import Lifecycles
from amt.api.navigation import BaseNavigationItem, DisplayText
from amt.core.authorization import AuthorizationResource, AuthorizationVerb
from amt.enums.tasks import TaskType
from amt.models import Algorithm, Authorization, Organization, Role, Rule, Task, User
from amt.schema.instrument import Instrument, InstrumentTask, Owner
from amt.schema.system_card import SystemCard
from fastapi import Request
from starlette.datastructures import URL


def default_auth_user() -> dict[str, Any]:
    return {
        "exp": 1732621076,
        "iat": 1732620776,
        "auth_time": 1732620601,
        "jti": "ad011860-aecb-4378-ba46-98284a7818f3",
        "iss": "https://keycloak.rig.prd1.gn2.quattro.rijksapps.nl/realms/amt-test",
        "aud": "AMT",
        "sub": "8eacad1c-594f-4507-bbd1-b162340d5984",
        "typ": "ID",
        "azp": "AMT",
        "nonce": "qZ9KGvZs6acg4nYENou5",
        "sid": "dd57ee84-8920-437e-bd86-35f7d306074f",
        "at_hash": "NI7WGdovQASx96dOg_wDlg",
        "acr": "0",
        "email_verified": True,
        "name": "Default User",
        "preferred_username": "default",
        "given_name": "Default",
        "family_name": "User",
        "email": "default@amt.nl",
        "email_hash": "a329108d9aabe362bc2fe4994989f6090b1445fd90ebe3520ab052f1836fa1a1",
        "name_encoded": "default+user",
    }


def default_base_navigation_item(
    url: str = "/default/",
    custom_display_text: str = "Default item",
    display_text: DisplayText | None = None,
    icon: str = "/icons/default.svg",
) -> BaseNavigationItem:
    return BaseNavigationItem(display_text=display_text, url=url, custom_display_text=custom_display_text, icon=icon)


def default_system_card() -> SystemCard:
    return SystemCard(  # pyright: ignore[reportCallIssue]
        name="Default System Card",
        description="Default system card",
    )


def default_algorithm(name: str = "default algorithm", organization_id: int = 1) -> Algorithm:
    return Algorithm(name=name, organization_id=organization_id, system_card=default_system_card())


def default_organization(name: str = "default organization", slug: str = "default-organization") -> Organization:
    return Organization(name=name, slug=slug, created_by_id=UUID(default_auth_user()["sub"]))


def default_rule() -> Rule:
    return Rule(
        resource=AuthorizationResource.ORGANIZATION_INFO,
        verbs=[AuthorizationVerb.CREATE, AuthorizationVerb.READ],
        role_id=1,
    )


def default_role() -> Role:
    return Role(name="default role")


def default_authorization(
    user_id: str | None = None, role_id: int | None = None, type: str | None = None, type_id: int | None = None
) -> Authorization:
    return Authorization(
        user_id=UUID(user_id) if user_id else UUID(default_auth_user()["sub"]),
        role_id=role_id if role_id else 1,
        type=type if type else "Organization",
        type_id=type_id if type_id else 1,
    )


def default_authorizations() -> list[Authorization]:
    return [
        Authorization(
            user_id=UUID(default_auth_user()["sub"]),
            role_id=1,
            type="Organization",
            type_id=1,
        ),
        Authorization(
            user_id=UUID(default_auth_user()["sub"]),
            role_id=4,
            type="Algorithm",
            type_id=1,
        ),
    ]


def default_user(
    id: str | UUID | None = None,
    name: str | None = None,
) -> User:
    user_name = name if name else default_auth_user()["name"]
    user_id = UUID(default_auth_user()["sub"]) if id is None else UUID(id) if isinstance(id, str) else id

    return User(
        id=user_id,
        name=user_name,
        email=default_auth_user()["email"],
        name_encoded=quote_plus(user_name.strip().lower()),
        email_hash=default_auth_user()["email_hash"],
    )


def default_user_without_default_organization(
    id: str | UUID | None = None,
    name: str | None = None,
) -> User:
    user_name = name if name else default_auth_user()["name"]
    user_id = UUID(default_auth_user()["sub"]) if id is None else UUID(id) if isinstance(id, str) else id

    return User(
        id=user_id,
        name=user_name,
        email=default_auth_user()["email"],
        name_encoded=quote_plus(user_name.strip().lower()),
        email_hash=default_auth_user()["email_hash"],
    )


def default_algorithm_with_system_card(name: str = "default algorithm") -> Algorithm:
    with open("resources/system_card_templates/AMT_Template_1.json") as f:
        system_card_from_template = json.load(f)
    system_card_from_template["name"] = name
    system_card = SystemCard.model_validate(system_card_from_template)
    return Algorithm(name=name, lifecycle=Lifecycles.DEVELOPMENT, system_card=system_card, organization_id=1)


def default_algorithm_with_lifecycle(
    name: str = "default algorithm", lifecycle: Lifecycles = Lifecycles.DESIGN, last_edited: datetime | None = None
) -> Algorithm:
    if last_edited:
        return Algorithm(name=name, lifecycle=lifecycle, organization_id=1, last_edited=last_edited)
    return Algorithm(name=name, lifecycle=lifecycle, organization_id=1)


def default_fastapi_request(url: str = "/") -> Request:
    request = Request(scope={"type": "http", "http_version": "1.1", "method": "GET", "headers": []})
    request.state.csrftoken = ""
    request._url = URL(url=url)  # pyright: ignore [reportPrivateUsage]
    return request


def default_instrument(
    urn: str = "urn1",
    description: str = "my instrument",
    name: str = "name1",
    language: str = "en",
    owners: list[Owner] = [],  # noqa: B006
    date: str = "1-1-1970",
    url: str = "https://1.com.html",
    tasks: list[InstrumentTask] = [],  # noqa: B006
) -> Instrument:
    return Instrument(
        urn=urn, description=description, name=name, language=language, owners=owners, date=date, url=url, tasks=tasks
    )


def default_task(
    title: str = "Default Task",
    description: str = "My default task",
    sort_order: float = 1.0,
    status_id: int | None = None,
    user_id: int | None = None,
    algorithm_id: int | None = None,
    type: TaskType | None = None,
    type_id: str | None = None,
) -> Task:
    return Task(
        title=title,
        description=description,
        sort_order=sort_order,
        status_id=status_id,
        user_id=user_id,
        algorithm_id=algorithm_id,
        type=type,
        type_id=type_id,
    )


TASK_REGISTRY_LIST_PAYLOAD = """
{
"entries": [
 {
      "type": "file",
      "size": 32897,
      "name": "iama.yaml",
      "path": "instruments/iama.yaml",
      "urn": "urn:nl:aivt:tr:iama:1.0",
      "download_url": "https://minbzk.github.io/task-registry/instruments/iama.yaml",
      "_links": {
        "self": "https://minbzk.github.io/task-registry/instruments/iama.yaml"
      }
    },
 {
      "type": "file",
      "size": 32897,
      "name": "aiia.yaml",
      "path": "instruments/aiia.yaml",
      "urn": "urn:nl:aivt:tr:aiia:1.0",
      "download_url": "https://minbzk.github.io/task-registry/instruments/aiia.yaml",
      "_links": {
        "self": "https://minbzk.github.io/task-registry/instruments/aiia.yaml"
      }
    }
]
}
"""

TASK_REGISTRY_MEASURES_LIST_PAYLOAD = """
{
entries": [
    {
      "type": "file",
      "size": 2075,
      "name": "3-dat-03-persoonsgegevens-beschrijven.yaml",
      "path": "measures/3-dat-03-persoonsgegevens-beschrijven.yaml",
      "urn": "urn:nl:ak:mtr:dat-03",
      "download_url": "https://task-registry.rijksapp.nl/measures/urn/urn:nl:ak:mtr:dat-03",
      "links": {
        "self": "https://task-registry.rijksapp.nl/measures/urn/urn:nl:ak:mtr:dat-03"
      }
    }
]
}
"""

TASK_REGISTRY_REQUIREMENTS_LIST_PAYLOAD = """
{
"entries": [
    {
      "type": "file",
      "size": 2032,
      "name": "aia-08-transparantie-aan-gebruiksverantwoordelijken.yaml",
      "path": "requirements/aia-08-transparantie-aan-gebruiksverantwoordelijken.yaml",
      "urn": "urn:nl:ak:ver:aia-08",
      "download_url": "https://task-registry.rijksapp.nl/requirements/urn/urn:nl:ak:ver:aia-08",
      "links": {
        "self": "https://task-registry.rijksapp.nl/requirements/urn/urn:nl:ak:ver:aia-08"
      }
    }
]
}
"""

TASK_REGISTRY_CONTENT_PAYLOAD = """
{
  "systemcard_path": ".assessments[]",
  "schema_version": "1.1.0",
  "name": "Impact Assessment Mensenrechten en Algoritmes (IAMA)",
  "description": "Het IAMA helpt om de risico's voor mensenrechten bij het gebruik van algoritmen \
          in kaart te brengen en maatregelen te nemen om deze aan te pakken.",
  "urn": "urn:nl:aivt:tr:iama:1.0",
  "language": "nl",
  "owners": [
    {
      "organization": "",
      "name": "",
      "email": "",
      "role": ""
    }
  ],
  "date": "",
  "url": "https://www.rijksoverheid.nl/documenten/rapporten/2021/02/25/impact-assessment-mensenrechten-en-algoritmes",
  "tasks": []
}
"""

TASK_REGISTRY_AIIA_CONTENT_PAYLOAD = """
{
  "systemcard_path": ".assessments[]",
  "schema_version": "1.1.0",
  "name": "AI Impact Assessment (AIIA)",
  "description": "Het IAMA helpt om de risico's voor mensenrechten bij het gebruik van algoritmen \
          in kaart te brengen en maatregelen te nemen om deze aan te pakken.",
  "urn": "urn:nl:aivt:tr:aiia:1.0",
  "language": "nl",
  "owners": [
    {
      "organization": "",
      "name": "",
      "email": "",
      "role": ""
    }
  ],
  "date": "",
  "url": "https://www.rijksoverheid.nl/documenten/rapporten/2021/02/25/impact-assessment-mensenrechten-en-algoritmes",
  "tasks": []
}
"""

TASK_REGISTRY_REQ_CONTENT_PAYLOAD = """
{
  "name": "Hoog-risico-AI-systemen zijn op een transparante manier ontwikkeld en ontworpen",
  "description": "AI-systemen met een hoog risico worden op zodanige wijze ontworpen en ontwikkeld dat de werking \
          ervan voldoende transparant is om gebruiksverantwoordelijken in staat te stellen de output van een \
          systeem te interpreteren en op passende wijze te gebruiken.Een passende soort en mate van \
          transparantie wordt gewaarborgd met het oog op de naleving van de relevante verplichtingen \
          van de aanbieder en de gebruiksverantwoordelijke zoals uiteengezet in afdeling 3 van Artikel\
          13 van de AI verordening.",
  "urn": "urn:nl:ak:ver:aia-08"
}
"""


def default_systemcard_dic() -> dict[str, str | list[Any] | None]:
    return {
        "version": "0.0.0",
        "provenance": None,
        "name": None,
        "instruments": [],
        "upl": None,
        "owners": [],
        "description": None,
        "ai_act_profile": None,
        "labels": [],
        "status": None,
        "begin_date": None,
        "end_date": None,
        "goal_and_impact": None,
        "considerations": None,
        "risk_management": None,
        "human_intervention": None,
        "legal_base": None,
        "used_data": None,
        "technical_design": None,
        "external_providers": None,
        "interaction_details": None,
        "version_requirements": None,
        "deployment_variants": None,
        "hardware_requirements": None,
        "product_markings": None,
        "user_interface": None,
        "schema_version": "0.1a10",
        "requirements": [],
        "measures": [],
        "assessments": [],
        "references": [],
        "models": [],
    }


def default_not_found_no_permission_msg() -> bytes:
    return b"We couldn't find what you were looking for. This might be because:"
