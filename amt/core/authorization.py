from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any

from starlette.requests import Request


def get_user(request: Request) -> dict[str, str] | None:
    user = None
    if isinstance(request.scope, Iterable) and "session" in request.scope:
        user = request.session.get("user", None)
    return user


def no_authorization(func: Callable[..., Any]):  # noqa: ANN201
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        request: Request = kwargs.get("request")  # type: ignore
        if request:
            request.state.noauth = True
        return await func(*args, **kwargs)

    return wrapper
