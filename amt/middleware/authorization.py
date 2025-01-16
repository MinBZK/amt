import os
import typing
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from amt.core.authorization import get_user
from amt.models import User
from amt.services.authorization import AuthorizationService

RequestResponseEndpoint = typing.Callable[[Request], typing.Awaitable[Response]]


class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in ["/auth/login", "/auth/logout", "/auth/callback", "/health/live", "/health/ready", "/"]:
            return await call_next(request)

        if request.url.path.startswith("/static/"):
            return await call_next(request)

        authorization_service = AuthorizationService()

        disable_auth_str = os.environ.get("DISABLE_AUTH")
        auth_disable = False if disable_auth_str is None else disable_auth_str.lower() == "true"
        if auth_disable:
            auto_login_uuid: str | None = os.environ.get("AUTO_LOGIN_UUID", None)
            if auto_login_uuid:
                user_object: User | None = await authorization_service.get_user(UUID(auto_login_uuid))
                if user_object:
                    request.session["user"] = {
                        "sub": str(user_object.id),
                        "email": user_object.email,
                        "name": user_object.name,
                        "email_hash": user_object.email_hash,
                        "name_encoded": user_object.name_encoded,
                    }
                else:
                    request.session["user"] = {"sub": auto_login_uuid}

        user = get_user(request)

        request.state.permissions = await authorization_service.find_by_user(user)

        if user:  # pragma: no cover
            return await call_next(request)

        response = await call_next(request)

        if auth_disable:
            return response

        return RedirectResponse(url="/")
