from typing import Any

from starlette.requests import Request
from starlette.responses import HTMLResponse

from amt.api.deps import templates
from amt.api.editable import get_enriched_resolved_editable, get_resolved_editables, save_editable
from amt.api.editable_classes import EditModes, FormState, ResolvedEditable
from amt.core.authorization import get_user
from amt.core.exceptions import AMTError
from amt.services.algorithms import AlgorithmsService
from amt.services.organizations import OrganizationsService
from amt.services.tasks import TasksService


async def update_handler(  # noqa: C901
    request: Request,
    full_resource_path: str,
    base_href: str,
    current_state_str: str,
    context_variables: dict[str, str | int],
    algorithms_service: AlgorithmsService | None,
    organizations_service: OrganizationsService | None,
    tasks_service: TasksService | None,
) -> HTMLResponse:
    user_id = get_user_id_or_error(request)
    new_values = await request.json()
    current_state = FormState.from_string(current_state_str)

    editable: ResolvedEditable = await get_enriched_resolved_editable(
        context_variables=context_variables,
        full_resource_path=full_resource_path,
        algorithms_service=algorithms_service,
        organizations_service=organizations_service,
        edit_mode=EditModes.SAVE,
    )

    editable_context: dict[str, Any] = {
        "user_id": user_id,
        "new_values": new_values,
        "organizations_service": organizations_service,
        "algorithms_service": algorithms_service,
        "tasks_service": tasks_service,
    }

    if current_state.is_validate():
        # if validations fail, an exception is thrown and handled by the exception handler
        await editable.validate(editable_context)
        # if validation succeeds, we automatically continue to the next state
        current_state = FormState.get_next_state(current_state)

    while current_state.is_before_save():
        if editable.has_hook(current_state):
            result = await editable.run_hook(current_state, request, templates, editable, editable_context)
            if result is not None:
                return result
        # if no hook exists or no hook returns a response, we automatically continue to the next state
        current_state = FormState.get_next_state(current_state)

    if current_state.is_save():
        editable = await save_editable(
            editable,
            editable_context=editable_context,
            algorithms_service=algorithms_service,
            organizations_service=organizations_service,
            do_save=True,
        )
        current_state = FormState.get_next_state(current_state)

    if current_state.is_after_save():
        while current_state is not FormState.COMPLETED:
            if editable.has_hook(current_state):
                result = await editable.run_hook(current_state, request, templates, editable, editable_context)
                if result is not None:
                    return result
            # if no hook exists or no hook returns a response, we automatically continue to the next state
            current_state = FormState.get_next_state(current_state)

    # If below is true, the default save was executed and there are no after save hooks or
    # none of the hooks returned a 'not None' response. We then return the default response.
    # We return this response here instead of at the default save action itself, because
    # post save hooks must be executed before we can return the response
    if current_state is FormState.COMPLETED:
        # set the value back to view mode if needed
        sub_editables = (editable.children or []) + (list(editable.couples) or [])
        if sub_editables:
            for sub_editable in sub_editables:
                if sub_editable.converter:
                    sub_editable.value = await sub_editable.converter.view(sub_editable.value, **editable_context)
        else:
            if editable.converter:
                editable.value = await editable.converter.view(editable.value, **editable_context)

        context = {
            "relative_resource_path": editable.relative_resource_path if editable.relative_resource_path else "",
            "base_href": base_href,
            "resource_object": editable.resource_object,
            "full_resource_path": full_resource_path,
            "editable_object": editable,
            "editables": get_resolved_editables(context_variables=context_variables),
        }

        return templates.TemplateResponse(request, "parts/view_cell.html.j2", context)
    return templates.TemplateResponse(request, "parts/view_cell.html.j2", {})


def get_user_id_or_error(request: Request) -> str:
    user = get_user(request)
    if user is None or user["sub"] is None:
        raise AMTError
    return user["sub"]
