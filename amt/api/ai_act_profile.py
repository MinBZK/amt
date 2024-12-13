from collections.abc import Iterable
from enum import Enum
from gettext import NullTranslations

from fastapi import Request

from amt.core.internationalization import get_current_translation


class AiActProfileItem(Enum):
    TYPE = "type"
    OPEN_SOURCE = "open_source"
    RISK_GROUP = "risk_group"
    CONFORMITY_ASSESSMENT_BODY = "conformity_assessment_body"
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
        case AiActProfileItem.RISK_GROUP:
            return _("In what risk group falls the application?")
        case AiActProfileItem.CONFORMITY_ASSESSMENT_BODY:
            return _("Does a conformity assessment need to be performed by an accredited body")
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
    radio_select: list[SelectAiProfileItem] | None
    multiple_select: list[SelectAiProfileItem] | None
    binary_select: list[SelectAiProfileItem] | None
    dropdown_select: list[SelectAiProfileItem] | None

    def __init__(
        self,
        radio_select: list[SelectAiProfileItem] | None = None,
        multiple_select: list[SelectAiProfileItem] | None = None,
        dropdown_select: list[SelectAiProfileItem] | None = None,
        binary_select: list[SelectAiProfileItem] | None = None,
    ) -> None:
        self.radio_select = radio_select
        self.dropdown_select = dropdown_select
        self.multiple_select = multiple_select
        self.binary_select = binary_select


def get_ai_act_profile_selector(request: Request) -> AiActProfileSelector:
    type_options = (
        "AI-systeem",
        "AI-systeem voor algemene doeleinden",
        "AI-model voor algemene doeleinden",
        "impactvol algoritme",
        "niet-impactvol algoritme",
        "geen algoritme",
    )

    role_options = (
        "aanbieder",
        "gebruiksverantwoordelijke",
        "importeur",
        "distributeur",
    )

    risk_group_options = (
        "hoog-risico AI",
        "geen hoog-risico AI",
        "verboden AI",
        "uitzondering van toepassing",
        "niet van toepassing",
    )

    conformity_assessment_body_options = ("beoordeling door derde partij", "niet van toepassing")

    systemic_risk_options = ("systeemrisico", "geen systeemrisico", "niet van toepassing")
    transparency_obligations_options = (
        "transparantieverplichting",
        "geen transparantieverplichting",
        "niet van toepassing",
    )
    open_source_options = ("open-source", "geen open-source", "niet van toepassing")

    translations = get_current_translation(request)

    return AiActProfileSelector(
        multiple_select=[
            SelectAiProfileItem(AiActProfileItem.ROLE, role_options, translations),
        ],
        dropdown_select=[
            SelectAiProfileItem(AiActProfileItem.TYPE, type_options, translations),
            SelectAiProfileItem(AiActProfileItem.RISK_GROUP, risk_group_options, translations),
            SelectAiProfileItem(
                AiActProfileItem.TRANSPARENCY_OBLIGATIONS, transparency_obligations_options, translations
            ),
            SelectAiProfileItem(AiActProfileItem.SYSTEMIC_RISK, systemic_risk_options, translations),
            SelectAiProfileItem(AiActProfileItem.OPEN_SOURCE, open_source_options, translations),
            SelectAiProfileItem(
                AiActProfileItem.CONFORMITY_ASSESSMENT_BODY, conformity_assessment_body_options, translations
            ),
        ],
        radio_select=[],
        binary_select=[],
    )
