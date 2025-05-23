from typing import Any, cast

from fastapi import Request
from fastapi.exceptions import RequestValidationError

from amt.api.editable_classes import EditableEnforcer, EditableValidator, EditModes, ResolvedEditable
from amt.core.authorization import AuthorizationType
from amt.core.dynamic_translations import ExternalFieldsTranslations
from amt.core.exceptions import AMTAuthorizationError, AMTRepositoryError
from amt.models import Authorization
from amt.services.algorithms import AlgorithmsService
from amt.services.authorization import AuthorizationsService
from amt.services.organizations import OrganizationsService
from amt.services.services_provider import ServicesProvider


class EditableEnforcerMustHaveMaintainer(EditableEnforcer):
    async def enforce(
        self,
        request: Request,
        editable: ResolvedEditable,
        editable_context: dict[str, Any],
        edit_mode: EditModes,
        services_provider: ServicesProvider,
    ) -> None:
        if edit_mode == EditModes.EDIT or edit_mode == EditModes.DELETE:
            authorizations_service = await services_provider.get(AuthorizationsService)
            in_value = EditableValidator.get_new_value(editable, editable_context)
            filters = {}
            maintainer_role_id = 0
            object_type = None
            object_type_id = None
            object_name = None
            if "organization_id" in editable_context:
                object_type = AuthorizationType.ORGANIZATION
                object_type_id = cast(int, editable_context["organization_id"])
                try:
                    object_name = (
                        await (await services_provider.get(OrganizationsService)).get_by_id(object_type_id)
                    ).name
                except AMTRepositoryError:
                    # If organization doesn't exist, we can skip the check
                    return
                maintainer_role_id = (await authorizations_service.get_role("Organization Maintainer")).id
            elif "algorithm_id" in editable_context:
                object_type = AuthorizationType.ALGORITHM
                object_type_id = cast(int, editable_context["algorithm_id"])
                try:
                    object_name = (await (await services_provider.get(AlgorithmsService)).get(object_type_id)).name
                except AMTRepositoryError:
                    # If algorithm doesn't exist, we can skip the check
                    return
                maintainer_role_id = (await authorizations_service.get_role("Algorithm Maintainer")).id
            # Only add filters if object_type and object_type_id are set
            filters: dict[str, str | int | list[str | int]] = {}
            if object_type is not None and object_type_id is not None:
                filters["type"] = str(object_type.value)
                filters["type_id"] = object_type_id

            authorizations = await authorizations_service.find_all(
                filters=filters,
            )
            maintainers_user_ids = [
                authorization.user_id
                for _, authorization, _, _ in authorizations
                if authorization.role_id == maintainer_role_id
            ]
            user_id = editable.get_resource_object(Authorization).user_id
            if (
                user_id in maintainers_user_ids
                and in_value != str(maintainer_role_id)
                and len(maintainers_user_ids) == 1
            ):
                errors = [
                    {
                        "loc": [editable.safe_html_path()],
                        "ctx": {
                            "type": ExternalFieldsTranslations.translate(object_type, request)
                            if object_type is not None
                            else "",
                            "type_name": object_name,
                        },
                        "type": "maintainer_role_required_with_context"
                        if object_type_id
                        else "maintainer_role_required",
                    }
                ]
                raise RequestValidationError(errors)


class EditableEnforcerMustHaveMaintainerForLists(EditableEnforcer):
    """
    When creating or updating members, at least one maintainer role is required.
    """

    async def enforce(
        self,
        request: Request,
        editable: ResolvedEditable,
        editable_context: dict[str, Any],
        edit_mode: EditModes,
        services_provider: ServicesProvider,
    ) -> None:
        if edit_mode == EditModes.EDIT or edit_mode == EditModes.SAVE_NEW:
            authorizations_service = await services_provider.get(AuthorizationsService)
            in_value = EditableValidator.get_new_value(editable, editable_context)
            authorization_type = AuthorizationType(cast(str, in_value[0]["type"]))
            type_id = int(in_value[0]["type_id"]) if "type_id" in in_value[0] and in_value[0]["type_id"] else 0
            if authorization_type == AuthorizationType.ORGANIZATION:
                maintainer_role_id = (await authorizations_service.get_role("Organization Maintainer")).id
            elif authorization_type == AuthorizationType.ALGORITHM:
                maintainer_role_id = (await authorizations_service.get_role("Algorithm Maintainer")).id
            else:
                raise TypeError("Unknown authorization type")
            new_maintainers_user_ids = [
                authorization["user_id"]
                for authorization in in_value
                if int(authorization["role_id"]) == maintainer_role_id
            ]
            if len(new_maintainers_user_ids) == 0:
                remaining_maintainers = []
                if type_id:
                    filters: dict[str, str | int | list[str | int]] = {
                        "type": str(authorization_type.value),
                        "type_id": type_id,
                    }
                    authorizations = await authorizations_service.find_all(filters=filters)
                    current_maintainers_user_ids = [
                        str(authorization.user_id)
                        for _, authorization, _, _ in authorizations
                        if authorization.role_id == maintainer_role_id
                    ]
                    new_roles_no_maintainer = [auth["user_id"] for auth in in_value]
                    remaining_maintainers = [
                        user_id for user_id in current_maintainers_user_ids if user_id not in new_roles_no_maintainer
                    ]
                if not remaining_maintainers:
                    errors = [{"loc": [editable.safe_html_path()], "type": "maintainer_role_required"}]
                    raise RequestValidationError(errors)


class EditableEnforcerForOrganizationInAlgorithm(EditableEnforcer):
    async def enforce(
        self,
        request: Request,
        editable: ResolvedEditable,
        editable_context: dict[str, Any],
        edit_mode: EditModes,
        services_provider: ServicesProvider,
    ) -> None:
        try:
            await (await services_provider.get(OrganizationsService)).find_by_id_and_user_id(
                organization_id=int(editable_context["new_values"]["organization"]),
                user_id=editable_context["user_id"],
            )
        except AMTRepositoryError as e:
            raise AMTAuthorizationError from e
