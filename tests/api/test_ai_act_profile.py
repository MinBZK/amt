from amt.api.ai_act_profile import (
    AiActProfileItem,
    get_translation,
)
from babel.support import Translations


def test_get_translation():
    translation = Translations.load("amt/locale", locales="en")
    for item in AiActProfileItem:
        assert get_translation(item, translation) is not None
    # empty match
    assert get_translation(None, translation) is None  # pyright: ignore
