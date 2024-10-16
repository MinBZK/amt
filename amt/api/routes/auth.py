import hashlib
import logging
from urllib.parse import quote_plus

from authlib.integrations.starlette_client import OAuth, OAuthError  # type: ignore
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from amt.api.deps import templates
from amt.core.authorization import get_user
from amt.core.exceptions import AMTAuthorizationFlowError

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
async def auth_callback(request: Request) -> Response:  # pragma: no cover
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

    if user:
        request.session["user"] = dict(user)  # type: ignore
        request.session["id_token"] = token["id_token"]  # type: ignore
    return RedirectResponse(url="/algorithm-systems/")


@router.get("/profile", response_class=Response)
async def auth_profile(request: Request) -> HTMLResponse:
    user = get_user(request)

    return templates.TemplateResponse(request, "auth/profile.html.j2", {"user": user})
