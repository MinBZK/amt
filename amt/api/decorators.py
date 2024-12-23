from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request

from amt.core.exceptions import AMTPermissionDenied


def add_permissions(permissions: dict[str, list[str]]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            request = kwargs.get("request")
            if not isinstance(request, Request):  # todo:  change exception to custom exception
                raise HTTPException(status_code=400, detail="Request object is missing")
            if request is None:
                raise HTTPException(status_code=400, detail="Request object is missing")

            # Add permissions to the request state
            request.state.permissions_needed = permissions
            for permission, verbs in permissions.items():
                if permission not in request.state.permissions:
                    raise AMTPermissionDenied()
                for verb in verbs:
                    if verb not in request.state.permissions[permission]:
                        raise AMTPermissionDenied()

            return await func(*args, **kwargs)

        return wrapper

    return decorator
