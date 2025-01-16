from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request

from amt.api.utils import SafeDict
from amt.core.exceptions import AMTPermissionDenied


def permission(permissions: dict[str, list[str]]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            request = kwargs.get("request")
            if not isinstance(request, Request):  # todo:  change exception to custom exception
                raise HTTPException(status_code=400, detail="Request object is missing")

            for permission, verbs in permissions.items():
                permission = permission.format_map(SafeDict(kwargs))
                request_permissions: dict[str, list[str]] = (
                    request.state.permissions if hasattr(request.state, "permissions") else {}
                )
                if permission not in request_permissions:
                    raise AMTPermissionDenied()
                for verb in verbs:
                    if verb not in request.state.permissions[permission]:
                        raise AMTPermissionDenied()

            return await func(*args, **kwargs)

        return wrapper

    return decorator
