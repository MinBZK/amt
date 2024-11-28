from gettext import NullTranslations

from amt.schema.webform import WebForm, WebFormField, WebFormFieldType, WebFormSearchField, WebFormSubmitButton


def get_organization_form(id: str, translations: NullTranslations) -> WebForm:
    _ = translations.gettext

    organization_form: WebForm = WebForm(id=id, post_url="/organizations/new")

    organization_form.fields = [
        WebFormField(
            type=WebFormFieldType.TEXT,
            name="name",
            label=_("Name"),
            placeholder=_("Name of the organization"),
            attributes={"onkeyup": "amt.generate_slug('" + id + "name', '" + id + "slug')"},
            group="1",
        ),
        WebFormField(
            type=WebFormFieldType.TEXT,
            name="slug",
            description=_("The slug is the web path, like /organizations/my-organization-name"),
            label=_("Slug"),
            placeholder=_("The slug for this organization"),
            group="1",
        ),
        WebFormSearchField(
            name="user_ids",
            label=_("Add members"),
            placeholder=_("Search for a person..."),
            search_url="/organizations/users?returnType=search_select_field",
            query_var_name="query",
            group="1",
        ),
        WebFormSubmitButton(label=_("Add organization"), group="1", name="submit"),
    ]
    return organization_form
