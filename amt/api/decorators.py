from collections import ChainMap
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import HTTPException, Request
from starlette.datastructures import State

from amt.api.utils import SafeDict
from amt.core.exceptions import AMTPermissionDenied
from amt.services.organizations import OrganizationsService
from amt.services.services_provider import ServicesProvider


def permission(permissions: dict[str, list[str]]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:  # noqa C901
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:  # noqa C901
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401 C901
            if not isinstance(kwargs.get("request"), Request):  # todo:  change exception to custom exception
                raise HTTPException(status_code=400, detail="Request object is missing")
            request: Request[State] = kwargs["request"]

            organization_slug_resolved = False
            extra_arguments: dict[str, Any] = {}
            for permission, verbs in permissions.items():
                # convert organization_slug to id if required
                if "organization_slug" in kwargs and "organization_slug" in permission:
                    if "organization_id" in kwargs:
                        permission = permission.replace("organization_slug", "organization_id")
                    else:
                        if not organization_slug_resolved:
                            service_provider = ServicesProvider()
                            async with service_provider.session_scope():
                                organization_service = await service_provider.get(OrganizationsService)
                                organization = await organization_service.find_by_slug(kwargs["organization_slug"])
                                extra_arguments["organization_id"] = organization.id
                                organization_slug_resolved = True
                        permission = permission.replace("organization_slug", "organization_id")

                permission = permission.format_map(SafeDict(ChainMap(kwargs, extra_arguments)))
                request_permissions: dict[str, list[str]] = getattr(request.state, "permissions", {})
                if permission not in request_permissions:
                    raise AMTPermissionDenied()
                for verb in verbs:
                    if verb not in request_permissions[permission]:
                        raise AMTPermissionDenied()

            return await func(*args, **kwargs)

        return wrapper

    return decorator
