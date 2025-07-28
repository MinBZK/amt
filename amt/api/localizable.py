from collections.abc import Callable
from enum import Enum
from typing import TypeVar

from fastapi import Request

from amt.core.internationalization import get_requested_language, get_supported_translation, get_translation
from amt.schema.localized_value_item import LocalizedValueItem

T = TypeVar("T", bound="LocalizableEnum", covariant=True)


class LocalizableEnum(Enum):
    @property
    def index(self) -> int:
        return list(self.__class__).index(self)

    def localize(self, language: str) -> LocalizedValueItem:
        translations = get_translation(get_supported_translation(language))
        _ = translations.gettext
        display_values = self.get_display_values(_)
        return LocalizedValueItem(value=self.name, display_value=display_values[self])

    @classmethod
    def get_display_values(cls: type[T], _: Callable[[str], str]) -> dict[T, str]:
        raise NotImplementedError("Subclasses must implement this method")


def get_localized_enum(key: LocalizableEnum | None, request: Request) -> LocalizedValueItem | None:
    """
    Given the key and translation, returns the translated text.
    :param key: the key
    :param request: request to get the current language
    :return: a LocalizedValueItem with the correct translation
    """
    if key is None:
        return None

    return key.localize(get_requested_language(request))


def get_localized_enums(enum_class: type[T], request: Request) -> list[LocalizedValueItem | None]:  # noqa UP047
    return [get_localized_enum(enum_value, request) for enum_value in enum_class]
