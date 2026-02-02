from collections.abc import Callable, Sequence
from os import PathLike
from typing import Any

import jinja_roos_components
from jinja2 import Environment, FileSystemLoader
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates, _TemplateResponse  # pyright: ignore[reportPrivateUsage]

from amt.core.internationalization import (
    get_requested_language,
    get_supported_translation,
    get_translation,
    supported_translations,
)


# we use a custom override so we can add the translation per request, which is parsed in the Request object in kwargs
class LocaleJinja2Templates(Jinja2Templates):
    def __init__(
        self,
        directory: str | PathLike[str] | Sequence[str | PathLike[str]],
        context_processors: list[Callable[[Request], dict[str, Any]]] | None = None,
        **env_options: Any,  # noqa: ANN401
    ) -> None:
        env = Environment(loader=FileSystemLoader(directory), autoescape=True, **env_options)
        env.add_extension("jinja2.ext.i18n")
        jinja_roos_components.setup_components(env, strict_validation=True)  # pyright: ignore [reportUnknownArgumentType]
        super().__init__(env=env, context_processors=context_processors)  # pyright: ignore[reportUnknownMemberType]

    def TemplateResponse(  # pyright: ignore [reportIncompatibleMethodOverride]
        self,
        request: Request,
        name: str,
        context: dict[str, Any] | None = None,
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
