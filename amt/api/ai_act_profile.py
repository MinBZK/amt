from collections.abc import Iterable
from enum import Enum
from gettext import NullTranslations

from fastapi import Request

from amt.core.internationalization import get_current_translation


class AiActProfileItem(Enum):
    TYPE = "type"
    OPEN_SOURCE = "open_source"
    PUBLICATION_CATEGORY = "publication_category"
    SYSTEMIC_RISK = "systemic_risk"
    TRANSPARENCY_OBLIGATIONS = "transparency_obligations"
    ROLE = "role"


def get_translation(item: AiActProfileItem, translations: NullTranslations) -> str:
    _ = translations.gettext
    match item:
        case AiActProfileItem.TYPE:
            return _("Type")
        case AiActProfileItem.OPEN_SOURCE:
            return _("Is the application open source?")
        case AiActProfileItem.PUBLICATION_CATEGORY:
            return _("Publication Category")
        case AiActProfileItem.SYSTEMIC_RISK:
            return _("Is there a systemic risk?")
        case AiActProfileItem.TRANSPARENCY_OBLIGATIONS:
            return _("Is there a transparency obligation?")
        case AiActProfileItem.ROLE:
            return _("Role")


class SelectAiProfileItem:
    display_name: str
    target_name: str
    options: Iterable[str] | None

    def __init__(
        self,
        item: AiActProfileItem,
        options: Iterable[str],
        translations: NullTranslations,
    ) -> None:
        self.display_name = get_translation(item, translations)
        self.target_name = item.value
        self.options = options


class AiActProfileSelector:
    multiple_select: list[SelectAiProfileItem] | None
    binary_select: list[SelectAiProfileItem] | None

    def __init__(
        self,
        multiple_select: list[SelectAiProfileItem] | None = None,
        binary_select: list[SelectAiProfileItem] | None = None,
    ) -> None:
        self.multiple_select = multiple_select
        self.binary_select = binary_select


def get_ai_act_profile_selector(request: Request) -> AiActProfileSelector:
    type_options = (
        "AI-systeem",
        "AI-systeem voor algemene doeleinden",
        "AI-model voor algemene doeleinden",
    )
    role_options = ("aanbieder", "gebruiksverantwoordelijke", "aanbieder + gebruiksverantwoordelijke")
    publication_category_options = (
        "impactvol algoritme",
        "niet-impactvol algoritme",
        "hoog-risico AI",
        "geen hoog-risico AI",
        "verboden AI",
    )
    open_source_options = ("open-source", "geen open-source")
    systemic_risk_options = ("systeemrisico", "geen systeemrisico")
    transparency_obligations_options = ("transparantieverplichtingen", "geen transparantieverplichtingen")

    translations = get_current_translation(request)

    return AiActProfileSelector(
        multiple_select=[
            SelectAiProfileItem(AiActProfileItem.TYPE, type_options, translations),
            SelectAiProfileItem(AiActProfileItem.ROLE, role_options, translations),
            SelectAiProfileItem(AiActProfileItem.PUBLICATION_CATEGORY, publication_category_options, translations),
        ],
        binary_select=[
            SelectAiProfileItem(
                AiActProfileItem.TRANSPARENCY_OBLIGATIONS, transparency_obligations_options, translations
            ),
            SelectAiProfileItem(AiActProfileItem.OPEN_SOURCE, open_source_options, translations),
            SelectAiProfileItem(AiActProfileItem.SYSTEMIC_RISK, systemic_risk_options, translations),
        ],
    )