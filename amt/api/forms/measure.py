from gettext import NullTranslations

from amt.schema.webform import WebForm, WebFormField, WebFormFieldType, WebFormOption, WebFormTextCloneableField


async def get_measure_form(
    id: str, current_values: dict[str, str | list[str]], translations: NullTranslations
) -> WebForm:
    _ = translations.gettext

    measure_form: WebForm = WebForm(id="", post_url="")

    measure_form.fields = [
        WebFormField(
            type=WebFormFieldType.SELECT,
            name="measure_state",
            label=_("Status"),
            options=[
                WebFormOption(value="to do", display_value="to do"),
                WebFormOption(value="in progress", display_value="in progress"),
                WebFormOption(value="done", display_value="done"),
            ],
            default_value=current_values.get("measure_state"),
            group="1",
        ),
        WebFormField(
            type=WebFormFieldType.TEXTAREA,
            name="measure_value",
            default_value=current_values.get("measure_value"),
            label=_("Information on how this measure is implemented"),
            placeholder=_("Describe how the measure has been implemented, including challenges and solutions."),
            group="1",
        ),
        WebFormField(
            type=WebFormFieldType.FILE,
            name="measure_files",
            default_value=current_values.get("measure_files"),
            label=_("Add files"),
            placeholder=_(""),
            group="1",
        ),
        WebFormTextCloneableField(
            clone_button_name=_("Add URI"),
            name="measure_links",
            default_value=current_values.get("measure_links"),
            label=_("Add links to documents"),
            placeholder=_("URI"),
            group="1",
        ),
    ]

    return measure_form
