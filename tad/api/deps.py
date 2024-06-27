import logging
import typing
from os import PathLike

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
from starlette.templating import _TemplateResponse  # type: ignore

from tad.core.config import VERSION
from tad.core.internationalization import (
    format_datetime,
    get_dynamic_field_translations,
    get_requested_language,
    get_supported_translation,
    get_translation,
    supported_translations,
)

logger = logging.getLogger(__name__)


def custom_context_processor(request: Request) -> dict[str, str | list[str] | dict[str, str]]:
    lang = get_requested_language(request)
    return {
        "version": VERSION,
        "available_translations": list(supported_translations),
        "language": lang,
        "translations": get_dynamic_field_translations(lang),
    }


# we use a custom override so we can add the translation per request, which is parsed in the Request object in kwargs
class LocaleJinja2Templates(Jinja2Templates):
    def _create_env(
        self,
        directory: str | PathLike[typing.AnyStr] | typing.Sequence[str | PathLike[typing.AnyStr]],
        **env_options: typing.Any,
    ) -> Environment:
        env: Environment = super()._create_env(directory, **env_options)  # type: ignore
        env.add_extension("jinja2.ext.i18n")  # type: ignore
        return env  # type: ignore

    def TemplateResponse(self, *args: typing.Any, **kwargs: typing.Any) -> _TemplateResponse:
        content_language = get_supported_translation(get_requested_language(kwargs["request"]))
        translations = get_translation(content_language)
        kwargs["headers"] = {"Content-Language": ",".join(supported_translations)}
        self.env.install_gettext_translations(translations, newstyle=True)  # type: ignore
        return super().TemplateResponse(*args, **kwargs)


templates = LocaleJinja2Templates(directory="tad/site/templates/", context_processors=[custom_context_processor])
templates.env.filters["format_datetime"] = format_datetime  # type: ignore
