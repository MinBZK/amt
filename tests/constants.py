from amt.api.navigation import BaseNavigationItem, DisplayText
from amt.models import Project, Task, User
from amt.schema.instrument import Instrument, InstrumentTask, Owner
from fastapi import Request
from starlette.datastructures import URL


def default_base_navigation_item(
    url: str = "/default/",
    custom_display_text: str = "Default item",
    display_text: DisplayText | None = None,
    icon: str = "/icons/default.svg",
) -> BaseNavigationItem:
    return BaseNavigationItem(display_text=display_text, url=url, custom_display_text=custom_display_text, icon=icon)


def default_user(name: str = "default user", avatar: str | None = None) -> User:
    return User(name=name, avatar=avatar)


def default_project(name: str = "default project", model_card: str = "/tmp/1.yaml") -> Project:  # noqa: S108
    return Project(name=name, model_card=model_card)


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
    project_id: int | None = None,
) -> Task:
    return Task(
        title=title,
        description=description,
        sort_order=sort_order,
        status_id=status_id,
        user_id=user_id,
        project_id=project_id,
    )


GITHUB_LIST_PAYLOAD = """
[
  {
    "name": "iama.yaml",
    "path": "instruments/iama.yaml",
    "sha": "50cf187eaea995ba848d93f1799fd34d4af8036b",
    "size": 30319,
    "url": "https://api.github.com/repos/MinBZK/task-registry/contents/instruments/iama.yaml?ref=main",
    "html_url": "https://github.com/MinBZK/task-registry/blob/main/instruments/iama.yaml",
    "git_url": "https://api.github.com/repos/MinBZK/task-registry/git/blobs/50cf187eaea995ba848d93f1799fd34d4af8036b",
    "download_url": "https://raw.githubusercontent.com/MinBZK/task-registry/main/instruments/iama.yaml",
    "type": "file",
    "_links": {
      "self": "https://api.github.com/repos/MinBZK/task-registry/contents/instruments/iama.yaml?ref=main",
      "git": "https://api.github.com/repos/MinBZK/task-registry/git/blobs/50cf187eaea995ba848d93f1799fd34d4af8036b",
      "html": "https://github.com/MinBZK/task-registry/blob/main/instruments/iama.yaml"
    }
  }
  ]
    """

GITHUB_CONTENT_PAYLOAD = """
systemcard_path: .assessments[]
schema_version: 1.1.0

name: "Impact Assessment Mensenrechten en Algoritmes (IAMA)"
description: "Het IAMA helpt om de risico's voor mensenrechten bij het gebruik van algoritmen in kaart te brengen en maatregelen te nemen om deze aan te pakken."
urn: "urn:nl:aivt:ir:iama:1.0"
language: "nl"
owners:
- organization: ""
  name: ""
  email: ""
  role: ""
date: ""
url: "https://www.rijksoverheid.nl/documenten/rapporten/2021/02/25/impact-assessment-mensenrechten-en-algoritmes"
tasks: []
"""  # noqa: E501
