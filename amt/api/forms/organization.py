from gettext import NullTranslations

from amt.api.editable_route_utils import create_editable_for_role
from amt.core.authorization import AuthorizationType
from amt.models import Organization, User
from amt.schema.webform import (
    WebForm,
    WebFormField,
    WebFormSearchField,
    WebFormSubmitButton,
)
from amt.schema.webform_classes import WebFormFieldType
from amt.services.authorization import AuthorizationsService
from fastapi import Request


async def get_organization_form(
    id: str, request: Request, translations: NullTranslations, user: User | None, organization: Organization | None
) -> WebForm:
    _ = translations.gettext

    if user is None:
        default_role = None
    else:
        organization_id = organization.id if organization else None
        from amt.services.services_provider import get_service_provider

        services_provider = await get_service_provider()
        authorizations_service = await services_provider.get(AuthorizationsService)
        role = await authorizations_service.get_role("Organization Maintainer")
        default_role = await create_editable_for_role(
            request,
            services_provider,
            user,
            AuthorizationType.ORGANIZATION,
            organization_id,
            role.id,
        )

    search_url = "/organizations/users?returnType=search_select_field"
    if organization:
        search_url += f"&organization_id={organization.id}"

    organization_form: WebForm = WebForm(id=id, post_url="/organizations/new")

    organization_form.fields = [
        WebFormField(
            type=WebFormFieldType.TEXT,
            name="name",
            label=_("Name"),
            placeholder="",
            attributes={"onkeyup": "amt.generate_slug('" + id + "name', '" + id + "slug')"},
            group="1",
            required=True,
        ),
        WebFormField(
            type=WebFormFieldType.TEXT,
            name="slug",
            description=_("The slug is the web path, like /organizations/my-organization-name"),
            label=_("Slug"),
            placeholder="",
            group="1",
            required=True,
        ),
        WebFormSearchField(
            name="user_ids",
            label=_("Add members"),
            placeholder="",
            # TODO: fix this URL with dynamic slug
            search_url=search_url,
            query_var_name="query",
            default_value=default_role,
            group="1",
        ),
        WebFormSubmitButton(label=_("Add organization"), group="1", name="submit"),
    ]
    return organization_form
