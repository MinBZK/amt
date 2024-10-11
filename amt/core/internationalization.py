import logging
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import yaml
from babel import dates
from babel.support import NullTranslations, Translations
from starlette.requests import Request

logger = logging.getLogger(__name__)

_default_language_fallback = "en"
supported_translations: tuple[str, ...] = ("en", "nl")


@lru_cache(maxsize=len(supported_translations))
def get_dynamic_field_translations(lang: str) -> dict[str, str]:
    lang = get_supported_translation(lang)
    with open(f"amt/languages/{lang}.yaml") as stream:
        return yaml.safe_load(stream)


def get_supported_translation(lang: str) -> str:
    if lang not in supported_translations:
        logger.warning("Requested translation does not exist: %s, using fallback %s", lang, _default_language_fallback)
        lang = _default_language_fallback
    return lang


@lru_cache(maxsize=len(supported_translations))
def get_translation(lang: str) -> NullTranslations:
    lang = get_supported_translation(lang)
    return Translations.load("amt/locale", locales=lang)


def get_current_translation(request: Request) -> NullTranslations:
    return get_translation(get_supported_translation(get_requested_language(request)))


def format_datetime(value: datetime, locale: str, format: str = "medium") -> str:
    if format == "full":
        format = "EEEE, d MMMM y HH:mm"
    elif format == "medium":
        format = "EE dd/MM/y HH:mm"
    else:
        format = "dd/MM/y HH:mm"
    return dates.format_datetime(value, format, locale=locale)


def format_timedelta(value: timedelta, locale: str = "en_US") -> str:
    # TODO: (Christopher) make this work
    return dates.format_timedelta(value, locale=locale)


def time_ago(value: datetime, locale: str) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)  # noqa: UP017
    return format_timedelta(datetime.now(tz=timezone.utc) - value, locale=locale)  # noqa: UP017


def get_browser_language_or_default(request: Request) -> str:
    # See https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Language
    languages = request.headers.get("Accept-Language", _default_language_fallback)
    return "nl" if languages.split(",")[0] in {"nl", "nl_NL"} else "en"


def get_requested_language(request: Request) -> str:
    lang = get_browser_language_or_default(request)

    return request.cookies.get("lang", lang)
