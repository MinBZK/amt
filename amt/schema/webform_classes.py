from dataclasses import dataclass
from enum import Enum
from typing import Any


class WebFormOption:
    value: str | Any
    display_value: str

    def __init__(self, value: str | Any, display_value: str) -> None:  # noqa: ANN401
        self.value = value
        self.display_value = display_value


class WebFormFieldType(Enum):
    CHECKBOX_MULTIPLE = "checkbox_multiple"
    HIDDEN = "hidden"
    TEXT = "text"
    TEXT_CLONEABLE = "text_cloneable"
    FILE = "file"
    RADIO = "radio"
    SELECT = "select"
    TEXTAREA = "textarea"
    DISABLED = "disabled"
    SEARCH_SELECT = "search_select"
    SUBMIT = "submit"
    DATE = "date"
    PRE_CHOSEN = "pre_chosen"


@dataclass
class WebFormFieldImplementationTypeFields:
    name: str
    type: WebFormFieldType | None


class WebFormFieldImplementationType:
    MULTIPLE_CHECKBOX_AI_ACT = WebFormFieldImplementationTypeFields("checkbox", WebFormFieldType.CHECKBOX_MULTIPLE)
    TEXT = WebFormFieldImplementationTypeFields("text", WebFormFieldType.TEXT)
    PARENT = WebFormFieldImplementationTypeFields("parent", None)
    TEXTAREA = WebFormFieldImplementationTypeFields("textarea", WebFormFieldType.TEXTAREA)
    SELECT_MY_ORGANIZATIONS = WebFormFieldImplementationTypeFields("select_my_organizations", WebFormFieldType.SELECT)
    SELECT_LIFECYCLE = WebFormFieldImplementationTypeFields("select_lifecycle", WebFormFieldType.SELECT)
    SELECT = WebFormFieldImplementationTypeFields("select", WebFormFieldType.SELECT)
    DATE = WebFormFieldImplementationTypeFields("date", WebFormFieldType.DATE)
    PRE_CHOSEN = WebFormFieldImplementationTypeFields("pre_chosen", WebFormFieldType.PRE_CHOSEN)
    HIDDEN = WebFormFieldImplementationTypeFields("hidden", WebFormFieldType.HIDDEN)
