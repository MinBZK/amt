from collections.abc import Iterable
from typing import Any

from starlette.requests import Request

from amt.core.internationalization import get_requested_language


def get_user(request: Request) -> dict[str, Any] | None:
    user = None
    if isinstance(request.scope, Iterable) and "session" in request.scope:
        user = request.session.get("user", None)
        if user:
            user["locale"] = get_requested_language(request)

    return user
