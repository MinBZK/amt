from gettext import NullTranslations
from uuid import UUID

from amt.schema.webform import WebForm, WebFormField, WebFormFieldType, WebFormOption
from amt.services.organizations import OrganizationsService


async def get_algorithm_form(
    id: str, translations: NullTranslations, organizations_service: OrganizationsService, user_id: str | UUID | None
) -> WebForm:
    _ = translations.gettext

    algorithm_form: WebForm = WebForm(id=id, post_url="")

    user_id = UUID(user_id) if isinstance(user_id, str) else user_id

    my_organizations = await organizations_service.get_organizations_for_user(user_id=user_id)

    select_organization: WebFormOption = WebFormOption(value="", display_value=_("Select organization"))

    algorithm_form.fields = [
        WebFormField(
            type=WebFormFieldType.SELECT,
            name="organization_id",
            label=_("Organization"),
            options=[select_organization]
            + [
                WebFormOption(value=str(organization.id), display_value=organization.name)
                for organization in my_organizations
            ],
            default_value="",
            group="1",
        ),
    ]

    return algorithm_form
