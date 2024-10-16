import logging
from enum import Enum

from fastapi import Request

from amt.core.internationalization import get_current_translation
from amt.schema.publication_category import PublicationCategory

logger = logging.getLogger(__name__)


class PublicationCategories(Enum):
    IMPACTVOL_ALGORITME = "impactvol algoritme"
    NIET_IMPACTVOL_ALGORITME = "niet-impactvol algoritme"
    HOOG_RISICO_AI = "hoog-risico AI"
    GEEN_HOOG_RISICO_AI = "geen hoog-risico AI"
    VERBODEN_AI = "verboden AI"
    UITZONDERING_VAN_TOEPASSING = "uitzondering van toepassing"


def get_publication_category(key: PublicationCategories | None, request: Request) -> PublicationCategory | None:
    """
    Given the key and translation, returns the translated text.
    :param key: the key
    :param request: request to get the current language
    :return: a Publication Category model with the correct translation
    """

    if key is None:
        return None

    translations = get_current_translation(request)
    _ = translations.gettext
    # translations are determined at runtime, which is why we use the dictionary below
    keys = {
        PublicationCategories.IMPACTVOL_ALGORITME: _("Impactful algorithm"),
        PublicationCategories.NIET_IMPACTVOL_ALGORITME: _("Non-impactful algorithm"),
        PublicationCategories.HOOG_RISICO_AI: _("High-risk AI"),
        PublicationCategories.GEEN_HOOG_RISICO_AI: _("No high-risk AI"),
        PublicationCategories.VERBODEN_AI: _("Forbidden AI"),
        PublicationCategories.UITZONDERING_VAN_TOEPASSING: _("Exception of application"),
    }
    return PublicationCategory(id=key.name, name=keys[key])


def get_publication_categories(request: Request) -> list[PublicationCategory | None]:
    return [get_publication_category(p, request) for p in PublicationCategories]
