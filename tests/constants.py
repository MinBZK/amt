import json
from uuid import UUID

from amt.api.lifecycles import Lifecycles
from amt.api.navigation import BaseNavigationItem, DisplayText
from amt.models import Algorithm, Task, User
from amt.schema.instrument import Instrument, InstrumentTask, Owner
from amt.schema.system_card import SystemCard
from fastapi import Request
from starlette.datastructures import URL


def default_base_navigation_item(
    url: str = "/default/",
    custom_display_text: str = "Default item",
    display_text: DisplayText | None = None,
    icon: str = "/icons/default.svg",
) -> BaseNavigationItem:
    return BaseNavigationItem(display_text=display_text, url=url, custom_display_text=custom_display_text, icon=icon)


def default_algorithm(name: str = "default algorithm") -> Algorithm:
    return Algorithm(name=name)


def default_user(id: str | UUID = "00494b4d-bcdf-425a-8140-bea0f3cbd3c2", name: str = "John Smith") -> User:
    id = UUID(id) if isinstance(id, str) else id
    return User(id=id, name=name)


def default_algorithm_with_system_card(name: str = "default algorithm") -> Algorithm:
    with open("resources/system_card_templates/AMT_Template_1.json") as f:
        system_card_from_template = json.load(f)
    system_card_from_template["name"] = name
    system_card = SystemCard.model_validate(system_card_from_template)
    return Algorithm(name=name, lifecycle=Lifecycles.DEVELOPMENT, system_card=system_card)


def default_algorithm_with_lifecycle(
    name: str = "default algorithm", lifecycle: Lifecycles = Lifecycles.DESIGN
) -> Algorithm:
    return Algorithm(name=name, lifecycle=lifecycle)


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
) -> Task:
    return Task(
        title=title,
        description=description,
        sort_order=sort_order,
        status_id=status_id,
        user_id=user_id,
        algorithm_id=algorithm_id,
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
      "download_url": "https://task-registry.apps.digilab.network/measures/urn/urn:nl:ak:mtr:dat-03",
      "links": {
        "self": "https://task-registry.apps.digilab.network/measures/urn/urn:nl:ak:mtr:dat-03"
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
      "download_url": "https://task-registry.apps.digilab.network/requirements/urn/urn:nl:ak:ver:aia-08",
      "links": {
        "self": "https://task-registry.apps.digilab.network/requirements/urn/urn:nl:ak:ver:aia-08"
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
