import hashlib
import logging
from typing import Annotated, Any
from urllib.parse import quote_plus
from uuid import UUID

from authlib.integrations.starlette_client import OAuth, OAuthError  # type: ignore
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from amt.api.deps import templates
from amt.api.editable_route_utils import get_user_id_or_error
from amt.core.authorization import AuthorizationType, get_user
from amt.core.exceptions import AMTAuthorizationFlowError
from amt.models.user import User
from amt.services.authorization import AuthorizationsService
from amt.services.services_provider import ServicesProvider, get_service_provider
from amt.services.users import UsersService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/login")
async def login(request: Request) -> HTMLResponse:  # pragma: no cover
    oauth: OAuth = request.app.state.oauth
    redirect_uri = request.url_for("auth_callback")
    return await oauth.keycloak.authorize_redirect(request, redirect_uri)  # type: ignore


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:  # pragma: no cover
    user = get_user(request)
    id_token = request.session.get("id_token", None)
    request.session.pop("user", None)
    request.session.pop("id_token", None)

    if user:
        redirect_uri = request.url_for("base")
        return RedirectResponse(
            url=user["iss"]
            + "/protocol/openid-connect/logout?id_token_hint="
            + id_token
            + "&post_logout_redirect_uri="
            + str(redirect_uri)
        )

    return RedirectResponse(url="/")


@router.get("/callback", response_class=Response)
async def auth_callback(
    request: Request,
    users_service: Annotated[UsersService, Depends(UsersService)],
) -> Response:  # pragma: no cover
    oauth: OAuth = request.app.state.oauth
    try:
        token = await oauth.keycloak.authorize_access_token(request)  # type: ignore
    except OAuthError as error:
        raise AMTAuthorizationFlowError() from error

    user: dict[str, str | int | bool] = token.get("userinfo")  # type: ignore
    if "email" in user and isinstance(user["email"], str):
        email: str = str(user["email"]).strip().lower()  # type: ignore
        user["email_hash"] = hashlib.sha256(email.encode()).hexdigest()

    if "name" in user and isinstance(user["name"], str):
        name: str = str(user["name"]).strip().lower()  # type: ignore
        user["name_encoded"] = quote_plus(name)

    if "sub" in user and isinstance(user["sub"], str):
        new_user = User(
            id=UUID(user["sub"]),  # type: ignore
            name=user["name"],
            email=user["email"],
            name_encoded=user["name_encoded"],
            email_hash=user["email_hash"],
        )
        # update the user in the database with (potential) new information
        await users_service.create_or_update(new_user)

    if user:
        request.session["user"] = dict(user)  # type: ignore
        request.session["id_token"] = token["id_token"]  # type: ignore
    return RedirectResponse(url="/algorithms/")


@router.get("/profile", response_class=Response)
async def auth_profile(
    request: Request,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    authorizations_service = await services_provider.get(AuthorizationsService)
    user_id = get_user_id_or_error(request)
    users_service = await services_provider.get(UsersService)
    user = users_service.find_by_id(user_id)
    filters: dict[str, Any] = {
        "type": AuthorizationType.ORGANIZATION,
        "user_id": UUID(user_id),
    }
    my_organizations = await authorizations_service.find_all(filters=filters)
    filters: dict[str, Any] = {
        "type": AuthorizationType.ALGORITHM,
        "user_id": UUID(user_id),
    }
    my_algorithms = await authorizations_service.find_all(filters=filters)

    context = {
        "user": user,
        "algorithms": my_algorithms,
        "organizations": my_organizations,
    }

    return templates.TemplateResponse(request, "auth/profile.html.j2", context)
