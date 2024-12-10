from collections.abc import Sequence
from gettext import NullTranslations

from amt.models import User
from amt.schema.webform import WebForm, WebFormField, WebFormFieldType, WebFormOption, WebFormTextCloneableField


async def get_measure_form(
    id: str,
    current_values: dict[str, str | list[str] | list[tuple[str, str]]],
    members: Sequence[User],
    translations: NullTranslations,
) -> WebForm:
    _ = translations.gettext

    measure_form: WebForm = WebForm(id="", post_url="")

    member_option_list = [WebFormOption(value=member.name, display_value=member.name) for member in members]
    member_option_list.append(WebFormOption(value="", display_value=""))
    measure_form.fields = [
        WebFormField(
            type=WebFormFieldType.SELECT,
            name="measure_responsible",
            label=_("Responsible"),
            options=member_option_list,
            default_value=current_values.get("measure_responsible"),
            group="1",
        ),
        WebFormField(
            type=WebFormFieldType.SELECT,
            name="measure_reviewer",
            label=_("Reviewer"),
            options=member_option_list,
            default_value=current_values.get("measure_reviewer"),
            group="1",
        ),
        WebFormField(
            type=WebFormFieldType.SELECT,
            name="measure_accountable",
            label=_("Accountable"),
            options=member_option_list,
            default_value=current_values.get("measure_accountable"),
            group="1",
        ),
        WebFormField(
            type=WebFormFieldType.SELECT,
            name="measure_state",
            label=_("Status"),
            options=[
                WebFormOption(value="to do", display_value="to do"),
                WebFormOption(value="in progress", display_value="in progress"),
                WebFormOption(value="in review", display_value="in review"),
                WebFormOption(value="done", display_value="done"),
                WebFormOption(value="not implemented", display_value="not implemented"),
            ],
            default_value=current_values.get("measure_state"),
            group="1",
        ),
        WebFormField(
            type=WebFormFieldType.TEXTAREA,
            name="measure_value",
            default_value=current_values.get("measure_value"),
            label=_("Information on how this measure is implemented"),
            placeholder="",
            group="1",
        ),
        WebFormField(
            type=WebFormFieldType.FILE,
            name="measure_files",
            description=_(
                "Select one or more to upload. The files will be saved once you confirm changes by pressing the save "
                "button."
            ),
            default_value=current_values.get("measure_files"),
            label=_("Add files"),
            placeholder=_("No files selected."),
            group="1",
        ),
        WebFormTextCloneableField(
            clone_button_name=_("Add URI"),
            name="measure_links",
            default_value=current_values.get("measure_links"),
            label=_("Add links to documents"),
            placeholder="",
            group="1",
        ),
    ]

    return measure_form
