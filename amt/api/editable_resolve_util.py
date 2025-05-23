from fastapi import Request

from amt.api.editable import enrich_editable, get_resolved_editables
from amt.api.editable_classes import EditModes, ResolvedEditable
from amt.api.editable_util import replace_digits_in_brackets
from amt.api.routes.shared import run_async_function  # pyright: ignore[reportUnknownVariableType]
from amt.services.services_provider import ServicesProvider


def resolve_editable_from_path(
    full_resource_path: str, context_variables: dict[str, str | int], request: Request
) -> ResolvedEditable | None:
    return run_async_function(_resolve_editable_from_path, full_resource_path, context_variables, request)  # pyright: ignore[reportUnknownVariableType]


async def _resolve_editable_from_path(
    full_resource_path: str, context_variables: dict[str, str | int], request: Request
) -> ResolvedEditable | None:
    resolved_editables = get_resolved_editables(context_variables)
    resolved_editable = resolved_editables.get(replace_digits_in_brackets(full_resource_path), None)
    if resolved_editable:
        services_provider = ServicesProvider()
        # we require a new session because we can not use the 'request' postgres session in another thread
        async with services_provider.session_scope():
            return await enrich_editable(
                resolved_editable, EditModes.VIEW, context_variables, services_provider, request, None
            )
    return None
