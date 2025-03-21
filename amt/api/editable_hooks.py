from typing import Any, cast

from starlette.requests import Request
from starlette.responses import HTMLResponse

from amt.api.editable_classes import EditableHook, ResolvedEditable
from amt.api.routes.shared import nested_value
from amt.api.template_classes import LocaleJinja2Templates
from amt.api.update_utils import set_path
from amt.api.utils import compare_lists
from amt.enums.tasks import TaskType
from amt.repositories.tasks import TasksRepository
from amt.schema.ai_act_profile import AiActProfile
from amt.schema.measure import MeasureTask
from amt.schema.requirement import RequirementTask
from amt.services.algorithms import AlgorithmsService, sort_by_measure_name
from amt.services.instruments_and_requirements_state import get_first_lifecycle_idx
from amt.services.measures import measures_service
from amt.services.requirements import requirements_service
from amt.services.task_registry import get_requirements_and_measures


class RedirectOrganizationHook(EditableHook):
    async def execute(
        self,
        request: Request,
        templates: LocaleJinja2Templates,
        editable: ResolvedEditable,
        editable_context: dict[str, str | dict[str, str]],
    ) -> HTMLResponse:
        return templates.Redirect(request, f"/organizations/{editable.value}")


class UpdateAIActHook(EditableHook):
    async def execute(
        self,
        request: Request,
        templates: LocaleJinja2Templates,
        editable: ResolvedEditable,
        editable_context: dict[str, str | dict[str, str]],
    ) -> None:
        new_values: dict[str, str] = cast(dict[str, str], editable_context.get("new_values", {}))

        if "algorithms_service" not in editable_context:
            raise TypeError("AlgorithmSService is missing but required")
        if "tasks_service" not in editable_context:
            raise TypeError("TasksService is missing but required")
        if not editable.resource_object:
            raise TypeError("ResourceObject is missing but required")

        current_requirements: list[RequirementTask] = nested_value(
            editable.resource_object, "system_card/requirements", []
        )
        current_measures: list[MeasureTask] = nested_value(editable.resource_object, "system_card/measures", [])
        (
            added_measures,
            added_requirements,
            removed_measures,
            removed_requirements,
        ) = await get_ai_act_differences(current_requirements, current_measures, new_values)

        # get urns of the removed items
        removed_requirements_urns = [item.urn for item in removed_requirements]
        # removed_measures_urns = [item.urn for item in removed_measures] # noqa ERA001

        # delete the removed items from the current sets
        updated_requirements = [task for task in current_requirements if task.urn not in removed_requirements_urns]
        # TODO: we do not remove measures at this point
        updated_measures = list(current_measures)  # if task.urn not in removed_measures_urns]

        # add new items to the current sets
        updated_requirements.extend(added_requirements)
        updated_measures.extend(added_measures)

        # update and save the systemcard
        set_path(editable.resource_object, "system_card/requirements", updated_requirements)
        set_path(editable.resource_object, "system_card/measures", updated_measures)
        await cast(AlgorithmsService, editable_context.get("algorithms_service")).update(editable.resource_object)

        # remove tasks from deleted measures
        await cast(TasksRepository, editable_context.get("tasks_service")).remove_tasks(
            editable.resource_object.id, TaskType.MEASURE, removed_measures
        )
        # add new tasks for added measures
        last_task = await cast(TasksRepository, editable_context.get("tasks_service")).get_last_task(
            editable.resource_object.id
        )
        start_at_sort_order = last_task.sort_order + 10 if last_task else 0
        measures_sorted: list[MeasureTask] = sorted(  # pyright: ignore[reportUnknownVariableType, reportCallIssue]
            added_measures,
            key=lambda measure: (get_first_lifecycle_idx(measure.lifecycle), sort_by_measure_name(measure)),  # pyright: ignore[reportArgumentType]
        )
        await cast(TasksRepository, editable_context.get("tasks_service")).add_tasks(
            editable.resource_object.id, TaskType.MEASURE, measures_sorted, start_at_sort_order
        )


class PreConfirmAIActHook(EditableHook):
    async def execute(
        self,
        request: Request,
        templates: LocaleJinja2Templates,
        editable: ResolvedEditable,
        editable_context: dict[str, str | dict[str, str]],
    ) -> HTMLResponse:
        new_values: dict[str, str] = cast(dict[str, str], editable_context.get("new_values", {}))
        headers = {"Hx-Trigger": "openModal", "HX-Reswap": "innerHTML", "HX-Retarget": "#dynamic-modal-content"}
        context: dict[str, Any] = {"new_values": new_values}

        current_requirements = nested_value(editable.resource_object, "system_card/requirements", [])
        current_measures = nested_value(editable.resource_object, "system_card/measures", [])

        (
            added_measures,
            added_requirements,
            removed_measures,
            removed_requirements,
        ) = await get_ai_act_differences(current_requirements, current_measures, new_values)

        added_requirements = await requirements_service.fetch_requirements([item.urn for item in added_requirements])
        removed_requirements = await requirements_service.fetch_requirements(
            [getattr(item, "urn", "") for item in removed_requirements]
        )
        added_measures = await measures_service.fetch_measures([item.urn for item in added_measures])
        removed_measures = await measures_service.fetch_measures([item.urn for item in removed_measures])

        context.update(
            {
                "added_requirements": added_requirements,
                "removed_requirements": removed_requirements,
                "added_measures": added_measures,
                "removed_measures": removed_measures,
            }
        )

        return templates.TemplateResponse(request, "algorithms/ai_act_changes_modal.html.j2", context, headers=headers)


async def get_ai_act_differences(
    current_requirements: list[RequirementTask],
    current_measures: list[MeasureTask],
    new_values: dict[str, str],
) -> tuple[list[MeasureTask], list[RequirementTask], list[MeasureTask], list[RequirementTask]]:
    ai_act_profile = AiActProfile(
        type=new_values.get("type"),
        open_source=new_values.get("open_source"),
        risk_group=new_values.get("risk_group"),
        conformity_assessment_body=new_values.get("conformity_assessment_body"),
        systemic_risk=new_values.get("systemic_risk"),
        transparency_obligations=new_values.get("transparency_obligations"),
        role=new_values.get("role"),
    )
    new_requirements, new_measures = await get_requirements_and_measures(ai_act_profile)
    added_requirements, removed_requirements = compare_lists(current_requirements, new_requirements, "urn", "urn")
    added_measures, removed_measures = compare_lists(current_measures, new_measures, "urn", "urn")
    return added_measures, added_requirements, removed_measures, removed_requirements
