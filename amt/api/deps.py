import logging
import typing
from os import PathLike

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, StrictUndefined, Undefined
from starlette.background import BackgroundTask
from starlette.templating import _TemplateResponse  # pyright: ignore [reportPrivateUsage]

from amt.api.http_browser_caching import url_for_cache
from amt.api.navigation import NavigationItem, get_main_menu
from amt.core.authorization import get_user
from amt.core.config import VERSION, get_settings
from amt.core.internationalization import (
    format_datetime,
    format_timedelta,
    get_current_translation,
    get_dynamic_field_translations,
    get_requested_language,
    get_supported_translation,
    get_translation,
    supported_translations,
    time_ago,
)

logger = logging.getLogger(__name__)


def custom_context_processor(
    request: Request,
) -> dict[str, str | None | list[str] | dict[str, str] | list[NavigationItem]]:
    lang = get_requested_language(request)
    translations = get_current_translation(request)
    return {
        "version": VERSION,
        "available_translations": list(supported_translations),
        "language": lang,
        "translations": get_dynamic_field_translations(lang),
        "main_menu_items": get_main_menu(request, translations),
        "user": get_user(request),
    }


def get_undefined_behaviour() -> type[Undefined]:
    return StrictUndefined if get_settings().DEBUG else Undefined


# we use a custom override so we can add the translation per request, which is parsed in the Request object in kwargs
class LocaleJinja2Templates(Jinja2Templates):
    def _create_env(
        self,
        directory: str | PathLike[typing.AnyStr] | typing.Sequence[str | PathLike[typing.AnyStr]],
        **env_options: typing.Any,  # noqa: ANN401
    ) -> Environment:
        env: Environment = super()._create_env(directory, **env_options)  # pyright: ignore [reportUnknownMemberType, reportUnknownVariableType, reportArgumentType]
        env.add_extension("jinja2.ext.i18n")  # pyright: ignore [reportUnknownMemberType]
        return env  # pyright: ignore [reportUnknownVariableType]

    def TemplateResponse(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        request: Request,
        name: str,
        context: dict[str, typing.Any] | None = None,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> _TemplateResponse:
        content_language = get_supported_translation(get_requested_language(request))
        translations = get_translation(content_language)
        if headers is None:
            headers = {}
        headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        if "Content-Language" not in headers:
            headers["Content-Language"] = ",".join(supported_translations)
        self.env.install_gettext_translations(translations, newstyle=True)  # pyright: ignore [reportUnknownMemberType]

        if context is None:
            context = {}

        if hasattr(request.state, "csrftoken"):
            context["csrftoken"] = request.state.csrftoken
        else:
            context["csrftoken"] = ""

        return super().TemplateResponse(request, name, context, status_code, headers, media_type, background)

    def Redirect(self, request: Request, url: str) -> HTMLResponse:
        headers = {"HX-Redirect": url}
        return self.TemplateResponse(request, "redirect.html.j2", headers=headers)


templates = LocaleJinja2Templates(
    directory="amt/site/templates/", context_processors=[custom_context_processor], undefined=get_undefined_behaviour()
)
templates.env.filters["format_datetime"] = format_datetime  # pyright: ignore [reportUnknownMemberType]
templates.env.filters["format_timedelta"] = format_timedelta  # pyright: ignore [reportUnknownMemberType]
templates.env.filters["time_ago"] = time_ago  # pyright: ignore [reportUnknownMemberType]
templates.env.globals.update(url_for_cache=url_for_cache)  # pyright: ignore [reportUnknownMemberType]
