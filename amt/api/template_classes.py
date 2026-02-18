import asyncio
from collections.abc import Callable, Mapping, Sequence
from os import PathLike
from typing import Any

import jinja_roos_components
from jinja2 import Environment, FileSystemLoader
from starlette.background import BackgroundTask
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from starlette.types import Receive, Scope, Send

from amt.core.internationalization import (
    get_requested_language,
    get_supported_translation,
    get_translation,
    supported_translations,
)


class _AsyncTemplateResponse(HTMLResponse):
    """A TemplateResponse that renders Jinja2 async templates.

    Unlike Starlette's default _TemplateResponse which renders synchronously in __init__,
    this defers rendering to __call__ (which is async) so that async template globals
    (like resolve_editable_from_path) can be awaited on the main event loop.
    """

    def __init__(
        self,
        template: Any,  # noqa: ANN401
        context: dict[str, Any],
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ) -> None:
        self.template = template
        self.context = context
        self._async_rendered = False
        try:
            asyncio.get_running_loop()
            # We're inside an async handler; defer rendering to __call__
            # where we can use render_async on the main event loop.
            content = ""
        except RuntimeError:
            # No running event loop (e.g. in tests); render synchronously.
            content = template.render(context)
            self._async_rendered = True
        super().__init__(content, status_code, headers, media_type, background)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self._async_rendered:
            # Render the template asynchronously on the main event loop.
            content = await self.template.render_async(self.context)
            self.body = content.encode("utf-8")
            self.headers["content-length"] = str(len(self.body))
            self._async_rendered = True

        request = self.context.get("request", {})
        extensions = request.get("extensions", {})
        if "http.response.debug" in extensions:
            await send(
                {
                    "type": "http.response.debug",
                    "info": {"template": self.template, "context": self.context},
                }
            )
        await super().__call__(scope, receive, send)


# we use a custom override so we can add the translation per request, which is parsed in the Request object in kwargs
class LocaleJinja2Templates(Jinja2Templates):
    def __init__(
        self,
        directory: str | PathLike[str] | Sequence[str | PathLike[str]],
        context_processors: list[Callable[[Request], dict[str, Any]]] | None = None,
        **env_options: Any,  # noqa: ANN401
    ) -> None:
        env = Environment(loader=FileSystemLoader(directory), autoescape=True, enable_async=True, **env_options)
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
    ) -> _AsyncTemplateResponse:
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

        context.setdefault("request", request)
        for context_processor in self.context_processors:
            context.update(context_processor(request))

        template = self.get_template(name)  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        return _AsyncTemplateResponse(
            template,
            context,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )

    def Redirect(self, request: Request, url: str) -> HTMLResponse:
        headers = {"HX-Redirect": url}
        return self.TemplateResponse(request, "redirect.html.j2", headers=headers)
