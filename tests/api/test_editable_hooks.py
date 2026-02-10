from typing import Any

import pytest
from amt.api.editable_classes import ResolvedEditable
from amt.api.editable_hooks import (
    PreConfirmAIActHook,
    RedirectMembersHook,
    RedirectOrganizationHook,
    SaveAuthorizationHook,
    UpdateAIActHook,
    get_ai_act_differences,
)
from amt.api.template_classes import LocaleJinja2Templates
from amt.core.authorization import AuthorizationType
from amt.schema.measure import MeasureTask
from amt.schema.requirement import (
    ConformityAssessmentBodyEnum,
    OpenSourceEnum,
    RequirementTask,
    RiskGroupEnum,
    RoleEnum,
    SystemicRiskEnum,
    TransparencyObligationEnum,
    TypeEnum,
)
from amt.schema.webform_classes import WebFormFieldImplementationType, WebFormOption
from amt.services.algorithms import AlgorithmsService
from amt.services.authorization import AuthorizationsService
from amt.services.measures import measures_service
from amt.services.requirements import requirements_service
from amt.services.services_provider import ServicesProvider
from amt.services.tasks import TasksService
from pytest_mock import MockerFixture

from tests.constants import default_algorithm, default_fastapi_request, default_organization


def default_resolved_editable() -> ResolvedEditable:
    return ResolvedEditable(
        full_resource_path="/algorithm/1/members",
        relative_resource_path="members",
        implementation_type=WebFormFieldImplementationType.TEXT,
    )


@pytest.mark.asyncio
async def test_save_authorization_hook_algorithm(mocker: MockerFixture):
    # Given
    hook = SaveAuthorizationHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)
    auth_service = mocker.MagicMock(spec=AuthorizationsService)

    user_id = "8eacad1c-594f-4507-bbd1-b162340d5984"
    mocker.patch.object(request, "json", return_value={"authorization": [{"user_id": user_id, "role_id": 1}]})

    service_provider.get.return_value = auth_service

    algorithm = default_algorithm()
    editable_context: dict[str, Any] = {"algorithm": algorithm}

    # When
    result = await hook.execute(request, templates, resolved_editable, editable_context, service_provider)

    # Then
    service_provider.get.assert_called_once_with(AuthorizationsService)
    auth_service.add_role_for_user.assert_called_once_with(user_id, 1, AuthorizationType.ALGORITHM, algorithm.id)
    assert result is None


@pytest.mark.asyncio
async def test_save_authorization_hook_organization(mocker: MockerFixture):
    # Given
    hook = SaveAuthorizationHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)
    auth_service = mocker.MagicMock(spec=AuthorizationsService)

    user_id = "8eacad1c-594f-4507-bbd1-b162340d5984"
    mocker.patch.object(request, "json", return_value={"authorization": [{"user_id": user_id, "role_id": 1}]})

    service_provider.get.return_value = auth_service

    organization = default_organization()
    editable_context: dict[str, Any] = {"organization": organization}

    # When
    result = await hook.execute(request, templates, resolved_editable, editable_context, service_provider)

    # Then
    service_provider.get.assert_called_once_with(AuthorizationsService)
    auth_service.add_role_for_user.assert_called_once_with(user_id, 1, AuthorizationType.ORGANIZATION, organization.id)
    assert result is None


@pytest.mark.asyncio
async def test_save_authorization_hook_no_auth_type(mocker: MockerFixture):
    # Given
    hook = SaveAuthorizationHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)
    auth_service = mocker.MagicMock(spec=AuthorizationsService)

    mocker.patch.object(
        request,
        "json",
        return_value={"authorization": [{"user_id": "8eacad1c-594f-4507-bbd1-b162340d5984", "role_id": 1}]},
    )

    service_provider.get.return_value = auth_service

    editable_context: dict[str, Any] = {}  # No algorithm or organization in context

    # When/Then
    with pytest.raises(TypeError, match="No authorization type provided"):
        await hook.execute(request, templates, resolved_editable, editable_context, service_provider)


@pytest.mark.asyncio
async def test_redirect_members_hook_algorithm(mocker: MockerFixture):
    # Given
    hook = RedirectMembersHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)

    algorithm = default_algorithm()
    algorithm.id = 123
    editable_context: dict[str, Any] = {"algorithm": algorithm}

    # When
    await hook.execute(request, templates, resolved_editable, editable_context, service_provider)

    # Then
    templates.Redirect.assert_called_once_with(request, "/algorithm/123/members")


@pytest.mark.asyncio
async def test_redirect_members_hook_organization(mocker: MockerFixture):
    # Given
    hook = RedirectMembersHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)

    organization = default_organization()
    organization.slug = "test-org"
    editable_context: dict[str, Any] = {"organization": organization}

    # When
    await hook.execute(request, templates, resolved_editable, editable_context, service_provider)

    # Then
    templates.Redirect.assert_called_once_with(request, "/organizations/test-org/members")


@pytest.mark.asyncio
async def test_redirect_members_hook_no_context(mocker: MockerFixture):
    # Given
    hook = RedirectMembersHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)

    editable_context: dict[str, Any] = {}  # No algorithm or organization in context

    # When/Then
    with pytest.raises(TypeError, match="Can not redirect if context does not contain 'organization' or 'algorithm'"):
        await hook.execute(request, templates, resolved_editable, editable_context, service_provider)


@pytest.mark.asyncio
async def test_redirect_organization_hook(mocker: MockerFixture):
    # Given
    hook = RedirectOrganizationHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)

    resolved_editable.value = WebFormOption(value="test-org", display_value="Test Org")
    editable_context: dict[str, Any] = {}

    # When
    await hook.execute(request, templates, resolved_editable, editable_context, service_provider)

    # Then
    templates.Redirect.assert_called_once_with(request, "/organizations/test-org")


@pytest.mark.asyncio
async def test_redirect_organization_hook_no_value(mocker: MockerFixture):
    # Given
    hook = RedirectOrganizationHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)

    resolved_editable.value = None
    editable_context: dict[str, Any] = {}

    # When/Then
    with pytest.raises(TypeError, match="Cannot redirect if editable value is None"):
        await hook.execute(request, templates, resolved_editable, editable_context, service_provider)


@pytest.mark.asyncio
async def test_update_ai_act_hook(mocker: MockerFixture):
    # Given
    hook = UpdateAIActHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)

    algorithm_service = mocker.MagicMock(spec=AlgorithmsService)
    tasks_service = mocker.MagicMock(spec=TasksService)

    service_provider.get.side_effect = [algorithm_service, tasks_service]

    # Mock for last task
    last_task = mocker.MagicMock()
    last_task.sort_order = 100
    tasks_service.get_last_task.return_value = last_task

    # Mock nested_value behavior for system_card requirements and measures
    requirements = [RequirementTask(urn="req1", version="1.0"), RequirementTask(urn="req2", version="1.0")]
    measures = [
        MeasureTask(urn="measure1", version="1.0", lifecycle=["DESIGN"]),
        MeasureTask(urn="measure2", version="1.0", lifecycle=["DESIGN"]),
    ]

    # Mock the resource_object directly
    resolved_editable.resource_object = mocker.MagicMock()
    mocker.patch(
        "amt.api.routes.shared.nested_value",
        side_effect=[
            requirements,  # First call for requirements
            measures,  # Second call for measures
        ],
    )

    # Create proper data objects for the diff returns with valid URNs
    # The format should match "urn:nl:ak:mtr:dat-03" pattern
    req_task1 = RequirementTask(urn="urn:nl:ak:ver:ver-03", version="1.0")
    measure_task1 = MeasureTask(urn="urn:nl:ak:mtr:dat-03", version="1.0", lifecycle=["DESIGN"])
    req_task2 = RequirementTask(urn="urn:nl:ak:ver:ver-02", version="1.0")
    measure_task2 = MeasureTask(urn="urn:nl:ak:mtr:dat-02", version="1.0", lifecycle=["DESIGN"])

    mocker.patch(
        "amt.api.editable_hooks.get_ai_act_differences",
        return_value=([measure_task1], [req_task1], [measure_task2], [req_task2]),
    )

    # Mock get_first_lifecycle_idx to avoid dependency issues
    mocker.patch("amt.services.instruments_and_requirements_state.get_first_lifecycle_idx", return_value=0)

    editable_context: dict[str, Any] = {
        "new_values": {
            "type": TypeEnum.AI_systeem.value,
            "risk_group": RiskGroupEnum.hoog_risico_AI.value,
            "open_source": OpenSourceEnum.geen_open_source.value,
            "conformity_assessment_body": ConformityAssessmentBodyEnum.beoordeling_door_derde_partij.value,
            "systemic_risk": SystemicRiskEnum.geen_systeemrisico.value,
            "transparency_obligations": TransparencyObligationEnum.transparantieverplichting.value,
            "role": RoleEnum.aanbieder.value,
        }
    }

    # When
    result = await hook.execute(request, templates, resolved_editable, editable_context, service_provider)

    # Then
    service_provider.get.assert_has_calls([mocker.call(AlgorithmsService), mocker.call(TasksService)])

    # Check that algorithm was updated with new requirements and measures
    algorithm_service.update.assert_called_once()

    # Check that tasks were removed and added
    tasks_service.remove_tasks.assert_called_once()
    tasks_service.add_tasks.assert_called_once()

    assert result is None


@pytest.mark.asyncio
async def test_update_ai_act_hook_no_resource_object(mocker: MockerFixture):
    # Given
    hook = UpdateAIActHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)

    algorithm_service = mocker.MagicMock(spec=AlgorithmsService)
    service_provider.get.return_value = algorithm_service

    resolved_editable.resource_object = None
    editable_context: dict[str, Any] = {
        "new_values": {"type": TypeEnum.AI_systeem.value, "risk_group": RiskGroupEnum.hoog_risico_AI.value}
    }

    # When/Then
    with pytest.raises(TypeError, match="ResourceObject is missing but required"):
        await hook.execute(request, templates, resolved_editable, editable_context, service_provider)


@pytest.mark.asyncio
async def test_pre_confirm_ai_act_hook(mocker: MockerFixture):
    # Given
    hook = PreConfirmAIActHook()
    resolved_editable = default_resolved_editable()
    request = default_fastapi_request()
    templates = mocker.MagicMock(spec=LocaleJinja2Templates)
    service_provider = mocker.MagicMock(spec=ServicesProvider)

    # Mock nested_value behavior for system_card requirements and measures
    requirements = [
        RequirementTask(urn="urn:nl:ak:ver:ver-01", version="1.0"),
        RequirementTask(urn="urn:nl:ak:ver:ver-02", version="1.0"),
    ]
    measures = [
        MeasureTask(urn="urn:nl:ak:mtr:dat-01", version="1.0", lifecycle=["DESIGN"]),
        MeasureTask(urn="urn:nl:ak:mtr:dat-02", version="1.0", lifecycle=["DESIGN"]),
    ]

    # Mock the resource_object directly
    resolved_editable.resource_object = mocker.MagicMock()
    mocker.patch(
        "amt.api.routes.shared.nested_value",
        side_effect=[
            requirements,  # First call for requirements
            measures,  # Second call for measures
        ],
    )

    # Create proper data objects for the diff returns with valid URNs
    req_task1 = RequirementTask(urn="urn:nl:ak:ver:ver-03", version="1.0")
    measure_task1 = MeasureTask(urn="urn:nl:ak:mtr:dat-03", version="1.0", lifecycle=["DESIGN"])
    req_task2 = RequirementTask(urn="urn:nl:ak:ver:ver-02", version="1.0")
    measure_task2 = MeasureTask(urn="urn:nl:ak:mtr:dat-02", version="1.0", lifecycle=["DESIGN"])

    mocker.patch(
        "amt.api.editable_hooks.get_ai_act_differences",
        return_value=([measure_task1], [req_task1], [measure_task2], [req_task2]),
    )

    # Mock requirements/measures services
    mocker.patch.object(requirements_service, "fetch_requirements", return_value=[req_task1])
    mocker.patch.object(measures_service, "fetch_measures", return_value=[measure_task1])

    editable_context: dict[str, Any] = {
        "new_values": {
            "type": TypeEnum.AI_systeem_voor_algemene_doeleinden.value,
            "risk_group": RiskGroupEnum.hoog_risico_AI.value,
            "open_source": OpenSourceEnum.open_source.value,
            "conformity_assessment_body": ConformityAssessmentBodyEnum.beoordeling_door_derde_partij.value,
            "systemic_risk": SystemicRiskEnum.systeemrisico.value,
            "transparency_obligations": TransparencyObligationEnum.transparantieverplichting.value,
            "role": RoleEnum.aanbieder.value,
        }
    }

    # When
    result = await hook.execute(request, templates, resolved_editable, editable_context, service_provider)

    # Then
    assert result
    templates.TemplateResponse.assert_called_once_with(
        request, "algorithms/ai_act_changes_modal.html.j2", mocker.ANY, headers=mocker.ANY
    )

    # Check context contains added/removed items
    context = templates.TemplateResponse.call_args.args[2]
    assert "added_requirements" in context
    assert "removed_requirements" in context
    assert "added_measures" in context
    assert "removed_measures" in context

    # Check headers
    headers = templates.TemplateResponse.call_args.kwargs["headers"]
    assert headers["Hx-Trigger"] == "openModal"
    assert headers["HX-Reswap"] == "innerHTML"
    assert headers["HX-Retarget"] == "#dynamic-modal-content"


@pytest.mark.asyncio
async def test_get_ai_act_differences(mocker: MockerFixture):
    # Given
    req_task1 = RequirementTask(urn="urn:nl:ak:ver:ver-01", version="1.0")
    req_task2 = RequirementTask(urn="urn:nl:ak:ver:ver-02", version="1.0")
    measure_task1 = MeasureTask(urn="urn:nl:ak:mtr:dat-01", version="1.0", lifecycle=["DESIGN"])
    measure_task2 = MeasureTask(urn="urn:nl:ak:mtr:dat-02", version="1.0", lifecycle=["DESIGN"])

    current_requirements = [req_task1, req_task2]
    current_measures = [measure_task1, measure_task2]

    new_values = {
        "type": TypeEnum.AI_systeem.value,
        "risk_group": RiskGroupEnum.hoog_risico_AI.value,
        "open_source": OpenSourceEnum.open_source.value,
        "conformity_assessment_body": ConformityAssessmentBodyEnum.beoordeling_door_derde_partij.value,
        "systemic_risk": SystemicRiskEnum.geen_systeemrisico.value,
        "transparency_obligations": TransparencyObligationEnum.transparantieverplichting.value,
        "role": RoleEnum.aanbieder.value,
    }

    req_task3 = RequirementTask(urn="urn:nl:ak:ver:ver-03", version="1.0")
    measure_task3 = MeasureTask(urn="urn:nl:ak:mtr:dat-03", version="1.0", lifecycle=["DESIGN"])

    new_requirements = [req_task1, req_task3]
    new_measures = [measure_task1, measure_task3]

    mocker.patch("amt.api.editable_hooks.get_requirements_and_measures", return_value=(new_requirements, new_measures))

    # When
    added_measures, added_requirements, removed_measures, removed_requirements = await get_ai_act_differences(
        current_requirements, current_measures, new_values
    )

    # Then
    assert len(added_measures) == 1
    assert added_measures[0].urn == "urn:nl:ak:mtr:dat-03"

    assert len(added_requirements) == 1
    assert added_requirements[0].urn == "urn:nl:ak:ver:ver-03"

    assert len(removed_measures) == 1
    assert removed_measures[0].urn == "urn:nl:ak:mtr:dat-02"

    assert len(removed_requirements) == 1
    assert removed_requirements[0].urn == "urn:nl:ak:ver:ver-02"
