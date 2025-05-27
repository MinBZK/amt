from collections.abc import Callable
from gettext import NullTranslations
from uuid import UUID

from amt.api.deps import permission
from amt.core.authorization import AuthorizationResource, AuthorizationVerb
from amt.models import Algorithm, Organization
from amt.schema.webform import (
    WebForm,
    WebFormField,
    WebFormSearchField,
)
from amt.schema.webform_classes import WebFormFieldType, WebFormOption
from amt.services.organizations import OrganizationsService


async def get_algorithm_form(
    id: str,
    translations: NullTranslations,
    organizations_service: OrganizationsService,
    user_id: str | UUID | None,
    organization_id: int | None,
    permissions: dict[str, list[AuthorizationVerb]],
) -> WebForm:
    if user_id is None:
        raise ValueError("user_id is required")

    _ = translations.gettext

    algorithm_form: WebForm = WebForm(id=id, post_url="")

    organization_select_field = await get_organization_select_field(
        _, organization_id, organizations_service, user_id, permissions
    )

    algorithm_form.fields = [organization_select_field]

    return algorithm_form


async def get_organization_select_field(
    _: Callable[[str], str],
    organization_id: int | None,
    organizations_service: OrganizationsService,
    user_id: str | UUID,
    permissions: dict[str, list[AuthorizationVerb]],
) -> WebFormField:
    user_id = UUID(user_id) if isinstance(user_id, str) else user_id
    all_organizations = await organizations_service.get_organizations_for_user(user_id=user_id)

    # only keep organization on which we have create permissions for algorithms
    my_organizations: list[Organization] = []
    for organization in all_organizations:
        resolved_permission = AuthorizationResource.ORGANIZATION_ALGORITHM.format_map(
            {"organization_id": organization.id}
        )
        has_create_permission = permission(resolved_permission, AuthorizationVerb.CREATE, permissions)
        if has_create_permission:
            my_organizations.append(organization)

    select_organization: WebFormOption = WebFormOption(value="", display_value=_("Select organization"))
    organization_select_field = WebFormField(
        type=WebFormFieldType.SELECT,
        name="organization_id",
        label=_("Organization"),
        no_options_msg=_(
            "You do not have sufficient permissions to create an algorithm on any organization you are member of"
        ),
        options=[select_organization]
        + [
            WebFormOption(value=str(organization.id), display_value=organization.name)
            for organization in my_organizations
        ],
        default_value=str(organization_id) if organization_id else "",
        group="1",
    )
    return organization_select_field


async def get_algorithm_members_form(
    id: str,
    translations: NullTranslations,
    algorithm: Algorithm,
) -> WebForm:
    _ = translations.gettext

    search_url = f"/algorithm/{algorithm.id}/users?returnType=search_select_field"

    add_members_form: WebForm = WebForm(id=id, post_url="/organizations/new")

    # TODO: this is a hack, because it is based on the organization form
    #  and it targets the 3rd field.. good enough for now
    add_members_form.fields = [
        None,
        None,
        WebFormSearchField(
            name="user_ids",
            label=_("Add members"),
            placeholder=_("Search for a person..."),
            search_url=search_url,
            query_var_name="query",
            default_value=None,
            group="1",
        ),
    ]
    return add_members_form
