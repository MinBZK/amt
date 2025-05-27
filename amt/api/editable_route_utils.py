from typing import Any

from starlette.requests import Request
from starlette.responses import HTMLResponse

from amt.api.deps import templates
from amt.api.editable import (
    Editables,
    enrich_editable,
    find_matching_editable,
    get_resolved_editable,
    get_resolved_editables,
    save_editable,
)
from amt.api.editable_classes import EditModes, FormState, ResolvedEditable
from amt.core.authorization import AuthorizationType, get_user
from amt.core.exceptions import AMTError
from amt.models import User
from amt.schema.webform_classes import WebFormOption
from amt.services.services_provider import ServicesProvider


async def update_handler(  # noqa: C901
    request: Request,
    full_resource_path: str,
    base_href: str,
    current_state_str: str,
    context_variables: dict[str, str | int],
    edit_mode: EditModes,
    services_provider: ServicesProvider,
) -> HTMLResponse:
    user_id = get_user_id_or_error(request)
    new_values = await request.json()
    current_state = FormState.from_string(current_state_str)
    context: dict[str, Any] = {}

    matched_editable, extracted_context_variables = find_matching_editable(full_resource_path)
    context_variables.update(extracted_context_variables)
    resolved_editable = get_resolved_editable(matched_editable, context_variables, True)
    editable = await enrich_editable(
        resolved_editable, edit_mode, {"user_id": user_id}, services_provider, request, None
    )

    editable_context: dict[str, Any] = {
        "user_id": user_id,
        "new_values": new_values,
    }
    # we add the context_variables which may be required later in the proces
    editable_context.update(context_variables)

    if current_state.is_validate():
        # if validations fail, an exception is thrown and handled by the exception handler
        await editable.validate(request, editable_context, services_provider, EditModes.EDIT)
        current_state = FormState.get_next_state(current_state)

    while current_state.is_before_save():
        if editable.has_hook(current_state):
            result = await editable.run_hook(
                current_state, request, templates, editable, editable_context, services_provider
            )
            if result is not None:
                return result
        current_state = FormState.get_next_state(current_state)

    if current_state.is_save():
        if editable.has_hook(current_state):
            result = await editable.run_hook(
                current_state, request, templates, editable, editable_context, services_provider
            )
            if result is not None:
                return result
        else:
            editable = await save_editable(
                editable,
                editable_context,
                EditModes.EDIT,
                request,
                True,
                services_provider,
            )
        current_state = FormState.get_next_state(current_state)

    if current_state.is_after_save():
        while True:
            if editable.has_hook(current_state):
                result = await editable.run_hook(
                    current_state, request, templates, editable, editable_context, services_provider
                )
                if result is not None:
                    return result
            if current_state is FormState.COMPLETED:
                break
            current_state = FormState.get_next_state(current_state)

    # Below is the default return behaviour, we end up here if no other previous hook returned a response

    # set the value back to view mode if needed
    # TODO: is this needed? does the save function not set the correct value already?
    all_editables = (editable.children or []) + (list(editable.couples) or [editable])
    for sub_editable in all_editables:
        if not isinstance(sub_editable.value, WebFormOption) and sub_editable.converter:
            sub_editable.value = await sub_editable.converter.view(
                sub_editable.value, request, sub_editable, editable_context, services_provider
            )

    context.update(
        {
            # TODO: SET PERMISSION FOR EACH EDITABLE!!
            "has_permission": True,
            "relative_resource_path": editable.relative_resource_path if editable.relative_resource_path else "",
            "base_href": base_href,
            "resource_object": editable.resource_object,
            "full_resource_path": full_resource_path,
            "editable_object": editable,
            "editables": get_resolved_editables(context_variables=context_variables),
        }
    )

    return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)


def get_user_id_or_error(request: Request) -> str:
    user = get_user(request)
    if user is None or "sub" not in user or user["sub"] is None:
        raise AMTError
    return user["sub"]


async def create_editable_for_role(
    request: Request,
    services_provider: ServicesProvider,
    user: User,
    type: AuthorizationType,
    type_id: int | None,
    role_id: int,
) -> ResolvedEditable:
    request.state.authorization_type = type
    user_id = get_user_id_or_error(request)
    custom_resource_object = {
        "user_id": WebFormOption(value=str(user.id), display_value=str(user.name)),
        "role_id": role_id,
        "type": type.value,
        "type_id": type_id,
    }
    context_variables: dict[str, str | int] = {}
    resolved_editable = get_resolved_editable(Editables.ROLE_EDITABLE, context_variables, False)
    enriched_editable = await enrich_editable(
        resolved_editable,
        EditModes.EDIT,
        {"user_id": user_id},
        services_provider,
        request,
        resource_object=custom_resource_object,
    )
    return enriched_editable
