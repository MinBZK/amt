from collections.abc import Iterable

from starlette.requests import Request


def get_user(request: Request) -> dict[str, str] | None:
    user = None
    if isinstance(request.scope, Iterable) and "session" in request.scope:
        user = request.session.get("user", None)
    return user
