from collections.abc import Iterable
from enum import StrEnum
from typing import Any

from starlette.requests import Request

from amt.core.internationalization import get_requested_language


class AuthorizationVerb(StrEnum):
    LIST = "List"
    READ = "Read"
    CREATE = "Create"
    UPDATE = "Update"
    DELETE = "Delete"


class AuthorizationType(StrEnum):
    ALGORITHM = "Algorithm"
    ORGANIZATION = "Organization"


class AuthorizationResource(StrEnum):
    ORGANIZATION_INFO = "organization/{organization_id}"
    ORGANIZATION_ALGORITHM = "organization/{organization_id}/algorithm"
    ORGANIZATION_MEMBER = "organization/{organization_id}/member"
    ALGORITHM = "algoritme/{algoritme_id}"
    ALGORITHM_SYSTEMCARD = "algoritme/{algoritme_id}/systemcard"
    ALGORITHM_MEMBER = "algoritme/{algoritme_id}/user"


def get_user(request: Request) -> dict[str, Any] | None:
    user = None
    if isinstance(request.scope, Iterable) and "session" in request.scope:
        user = request.session.get("user", None)
        if user:
            user["locale"] = get_requested_language(request)

    return user
