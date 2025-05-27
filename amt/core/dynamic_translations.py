from enum import StrEnum
from gettext import gettext as _
from typing import ClassVar

from fastapi import Request

from amt.core.authorization import AuthorizationType
from amt.core.internationalization import get_current_translation


class ExternalFieldsTranslations:
    TRANSLATIONS: ClassVar[dict[str | StrEnum, str]] = {
        "Organization Maintainer": _("Organization Maintainer"),
        "Organization Member": _("Organization Member"),
        "Organization Viewer": _("Organization Viewer"),
        "Algorithm Maintainer": _("Algorithm Maintainer"),
        "Algorithm Member": _("Algorithm Member"),
        "Algorithm Viewer": _("Algorithm Viewer"),
        AuthorizationType.ORGANIZATION: _("organization"),
        AuthorizationType.ALGORITHM: _("algorithm"),
    }

    @staticmethod
    def translate(key: str | StrEnum, request: Request | None) -> str:
        if not request:
            raise ValueError("Request is required to translate external fields")
        translations = get_current_translation(request)
        if key in ExternalFieldsTranslations.TRANSLATIONS:
            return translations.gettext(ExternalFieldsTranslations.TRANSLATIONS[key])
        return str(key)
