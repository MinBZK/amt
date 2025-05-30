from typing import Any

from amt.api.editable_classes import ResolvedEditable
from amt.schema.webform_classes import WebFormFieldType, WebFormOption


class WebFormBaseField:
    id: str
    type: WebFormFieldType
    name: str
    label: str
    group: str | None

    def __init__(self, type: WebFormFieldType, name: str, label: str, group: str | None = None) -> None:
        self.type = type
        self.label = label
        self.name = name
        self.group = group


class WebFormField(WebFormBaseField):
    placeholder: str | None
    default_value: str | list[str] | list[tuple[str, str]] | WebFormOption | ResolvedEditable | None
    options: list[WebFormOption] | None
    validators: list[Any]
    description: str | None
    attributes: dict[str, str] | None
    required: bool

    def __init__(
        self,
        type: WebFormFieldType,
        name: str,
        label: str,
        placeholder: str | None = None,
        default_value: str | list[str] | list[tuple[str, str]] | WebFormOption | ResolvedEditable | None = None,
        options: list[WebFormOption] | None = None,
        attributes: dict[str, str] | None = None,
        description: str | None = None,
        group: str | None = None,
        required: bool = False,
        no_options_msg: str | None = None,
    ) -> None:
        super().__init__(type=type, name=name, label=label, group=group)
        self.placeholder = placeholder
        self.default_value = default_value
        self.options = options
        self.attributes = attributes
        self.description = description
        self.required = required
        self.no_options_msg = no_options_msg


class WebFormSearchField(WebFormField):
    search_url: str
    query_var_name: str

    def __init__(
        self,
        query_var_name: str,
        search_url: str,
        name: str,
        label: str,
        placeholder: str | None = None,
        default_value: str | list[str] | list[tuple[str, str]] | WebFormOption | ResolvedEditable | None = None,
        options: list[WebFormOption] | None = None,
        attributes: dict[str, str] | None = None,
        group: str | None = None,
        description: str | None = None,
    ) -> None:
        super().__init__(
            type=WebFormFieldType.SEARCH_SELECT,
            name=name,
            label=label,
            placeholder=placeholder,
            default_value=default_value,
            options=options,
            attributes=attributes,
            group=group,
            description=description,
        )
        self.search_url = search_url
        self.query_var_name = query_var_name


class WebFormTextCloneableField(WebFormField):
    clone_button_name: str

    def __init__(
        self,
        clone_button_name: str,
        name: str,
        label: str,
        placeholder: str | None = None,
        default_value: str | list[str] | list[tuple[str, str]] | WebFormOption | ResolvedEditable | None = None,
        options: list[WebFormOption] | None = None,
        attributes: dict[str, str] | None = None,
        group: str | None = None,
        description: str | None = None,
    ) -> None:
        super().__init__(
            type=WebFormFieldType.TEXT_CLONEABLE,
            name=name,
            label=label,
            placeholder=placeholder,
            default_value=default_value,
            options=options,
            attributes=attributes,
            group=group,
            description=description,
        )
        self.clone_button_name = clone_button_name


class WebForm:
    id: str
    legend: str | None
    post_url: str
    fields: list[WebFormBaseField | None]

    def __init__(self, id: str, post_url: str, legend: str | None = None) -> None:
        self.id = id
        self.legend = legend
        self.post_url = post_url
        self.fields: list[WebFormBaseField | None] = []


class WebFormSubmitButton(WebFormBaseField):
    def __init__(self, label: str, name: str, group: str | None = None) -> None:
        super().__init__(type=WebFormFieldType.SUBMIT, name=name, label=label, group=group)
