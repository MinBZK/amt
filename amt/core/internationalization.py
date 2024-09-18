import logging
from datetime import datetime, timedelta
from functools import lru_cache

import yaml
from babel import dates
from babel.support import NullTranslations, Translations
from starlette.requests import Request

logger = logging.getLogger(__name__)

_default_language_fallback = "en"
supported_translations: tuple[str, ...] = ("en", "nl", "fy")
# babel does not support Frysian, to be able to load the right MO file, we need to 'map' it ourselves
_translations_to_locale: dict[str, str] = {"en": "en", "nl": "nl", "fy": "nl_FY"}


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
    return Translations.load("amt/locale", locales=_translations_to_locale[lang])


def get_current_translation(request: Request) -> NullTranslations:
    return get_translation(get_supported_translation(get_requested_language(request)))


def format_datetime(value: datetime, locale: str, format: str = "medium") -> str:
    if format == "full" and locale == "fy":
        weekday = get_dynamic_field_translations("fy")["weekdays"][int(datetime.date(value).strftime("%w"))]
        month = get_dynamic_field_translations("fy")["months"][int(datetime.date(value).strftime("%-m")) - 1]
        return value.strftime(f"{weekday}, %-d {month} %Y %H:%M")
    elif format == "medium" and locale == "fy":
        weekday = get_dynamic_field_translations("fy")["weekdays"][int(datetime.date(value).strftime("%w"))]
        return value.strftime(f"{weekday} %d-%m-%Y %H:%M")
    elif format == "full":
        format = "EEEE, d MMMM y HH:mm"
    elif format == "medium":
        format = "EE dd/MM/y HH:mm"
    else:
        format = "dd/MM/y HH:mm"
    return dates.format_datetime(value, format, locale=locale)


def format_timedelta(value: timedelta, locale: str = "en_US") -> str:
    # TODO: (Christopher) make this work
    return dates.format_timedelta(value, locale=locale)


def get_requested_language(request: Request) -> str:
    # todo (robbert): nice to have, default support based on accept lang of browser
    return request.cookies.get("lang", _default_language_fallback)
