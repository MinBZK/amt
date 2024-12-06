import pytest
from amt.schema.ai_act_profile import AiActProfile
from amt.schema.measure import Measure
from amt.schema.requirement import (
    OpenSourceEnum,
    Requirement,
    RequirementAiActProfile,
    RiskCategoryEnum,
    RoleEnum,
    SystemicRiskEnum,
    TransparencyObligation,
    TypeEnum,
)
from amt.services.task_registry import get_requirements_and_measures, is_requirement_applicable
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_is_requirement_applicable_empty_profile():
    # given
    ai_act_profile = AiActProfile()
    implicit_always_applicable_requirement = Requirement(
        name="requirement 1",
        urn="urn:requirement:1",
        description="description 1",
        schema_version="1.1.0",
        links=[],
        always_applicable=0,
        ai_act_profile=[
            RequirementAiActProfile(
                type=[],
                risk_category=[],
                role=[],
                open_source=[],
                systemic_risk=[],
                transparency_obligations=[],
            ),
        ],
    )
    explicit_always_applicable_requirement = Requirement(
        name="requirement 2",
        urn="urn:requirement:2",
        description="description 2",
        schema_version="1.1.0",
        links=[],
        always_applicable=1,
        ai_act_profile=[
            RequirementAiActProfile(
                type=[TypeEnum.AI_systeem],
                risk_category=[RiskCategoryEnum.hoog_risico_AI],
                role=[RoleEnum.gebruiksverantwoordelijke],
                open_source=[OpenSourceEnum.open_source],
                systemic_risk=[SystemicRiskEnum.systeemrisico],
                transparency_obligations=[TransparencyObligation.transparantieverplichting],
            ),
        ],
    )

    # when
    implicit_result = is_requirement_applicable(implicit_always_applicable_requirement, ai_act_profile)
    explicit_result = is_requirement_applicable(explicit_always_applicable_requirement, ai_act_profile)

    # then
    assert implicit_result is True
    assert explicit_result is True


@pytest.mark.asyncio
async def test_is_requirement_applicable_with_profile():
    # given
    ai_act_profile = AiActProfile(
        type="AI-systeem",
        risk_group="hoog-risico AI",
        conformity_assessment_body="beoordeling door derde partij",
        role="gebruiksverantwoordelijke",
        open_source="open-source",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichting",
    )

    requirement = Requirement(
        name="requirement 3",
        urn="urn:requirement:3",
        description="description 3",
        schema_version="1.1.0",
        links=[],
        always_applicable=0,
        ai_act_profile=[
            RequirementAiActProfile(
                type=[],
                risk_category=[
                    RiskCategoryEnum.hoog_risico_AI,
                    RiskCategoryEnum.verboden_AI,
                    RiskCategoryEnum.geen_hoog_risico_AI,
                ],
                role=[RoleEnum.gebruiksverantwoordelijke, RoleEnum.aanbieder],
                open_source=[],
                systemic_risk=[],
                transparency_obligations=[],
            ),
        ],
    )

    # when
    result = is_requirement_applicable(requirement, ai_act_profile)

    # then
    assert result is True


@pytest.mark.asyncio
async def test_is_requirement_applicable_with_profile_with_2_roles():
    # given
    ai_act_profile = AiActProfile(
        type="AI-model voor algemene doeleinden",
        risk_group="hoog-risico AI",
        role="aanbieder + gebruiksverantwoordelijke",
        open_source="geen open-source",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichting",
    )

    requirement = Requirement(
        name="requirement 3",
        urn="urn:requirement:3",
        description="description 3",
        schema_version="1.1.0",
        links=[],
        always_applicable=0,
        ai_act_profile=[
            RequirementAiActProfile(
                type=[],
                risk_category=[
                    RiskCategoryEnum.hoog_risico_AI,
                    RiskCategoryEnum.verboden_AI,
                    RiskCategoryEnum.geen_hoog_risico_AI,
                ],
                role=[RoleEnum.gebruiksverantwoordelijke, RoleEnum.aanbieder],
                open_source=[],
                systemic_risk=[],
                transparency_obligations=[],
            ),
        ],
    )

    # when
    result = is_requirement_applicable(requirement, ai_act_profile)

    # then
    assert result is True


@pytest.mark.asyncio
async def test_is_requirement_applicable_with_non_matching_profile():
    # given
    ai_act_profile = AiActProfile(
        type="AI-model voor algemene doeleinden",
        risk_group="hoog-risico AI",
        role="aanbieder + gebruiksverantwoordelijke",
        open_source="geen open-source",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichting",
    )

    requirement = Requirement(
        name="requirement 3",
        urn="urn:requirement:3",
        description="description 3",
        schema_version="1.1.0",
        links=[],
        always_applicable=0,
        ai_act_profile=[
            RequirementAiActProfile(
                type=[TypeEnum.AI_systeem],
                risk_category=[
                    RiskCategoryEnum.hoog_risico_AI,
                    RiskCategoryEnum.verboden_AI,
                    RiskCategoryEnum.geen_hoog_risico_AI,
                ],
                role=[RoleEnum.gebruiksverantwoordelijke, RoleEnum.aanbieder],
                open_source=[],
                systemic_risk=[],
                transparency_obligations=[],
            ),
        ],
    )

    # when
    result = is_requirement_applicable(requirement, ai_act_profile)

    # then
    assert result is False


@pytest.mark.asyncio
async def test_is_requirement_applicable_with_matching_profile():
    # given
    ai_act_profile = AiActProfile(
        type="AI-model voor algemene doeleinden",
        risk_group="hoog-risico AI",
        role="aanbieder",
        open_source="geen open-source",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichting",
    )

    requirement = Requirement(
        name="requirement 3",
        urn="urn:requirement:3",
        description="description 3",
        schema_version="1.1.0",
        links=[],
        always_applicable=0,
        ai_act_profile=[
            RequirementAiActProfile(
                type=[TypeEnum.AI_model_voor_algemene_doeleinden],
                risk_category=[RiskCategoryEnum.hoog_risico_AI],
                role=[RoleEnum.aanbieder],
                open_source=[OpenSourceEnum.geen_open_source],
                systemic_risk=[SystemicRiskEnum.systeemrisico],
                transparency_obligations=[TransparencyObligation.transparantieverplichting],
            ),
        ],
    )

    # when
    result = is_requirement_applicable(requirement, ai_act_profile)

    # then
    assert result is True


@pytest.mark.asyncio
async def test_get_requirements_and_measures_no_applicable_requirements(mocker: MockerFixture):
    mock_requirements_service = mocker.AsyncMock()
    mock_measures_service = mocker.AsyncMock()

    mocker.patch("amt.services.task_registry.create_requirements_service", return_value=mock_requirements_service)
    mocker.patch("amt.services.task_registry.create_measures_service", return_value=mock_measures_service)
    mocker.patch("amt.services.task_registry.is_requirement_applicable", return_value=False)

    mock_requirements_service.fetch_requirements.return_value = [
        Requirement(
            name="requirement",
            urn="urn:requirement:1",
            description="description",
            schema_version="1.1.0",
            links=[],
            always_applicable=0,
            ai_act_profile=[
                RequirementAiActProfile(
                    type=[],
                    risk_category=[],
                    role=[],
                    open_source=[],
                    systemic_risk=[],
                    transparency_obligations=[],
                ),
            ],
        ),
    ]

    ai_act_profile = AiActProfile()

    requirements, measures = await get_requirements_and_measures(ai_act_profile)

    assert requirements == []
    assert measures == []
    mock_requirements_service.fetch_requirements.assert_awaited_once()
    mock_measures_service.fetch_measures.assert_not_called()


@pytest.mark.asyncio
async def test_get_requirements_and_measures_single_requirement_with_measures(mocker: MockerFixture):
    mock_requirements_service = mocker.AsyncMock()
    mock_measures_service = mocker.AsyncMock()

    mocker.patch("amt.services.task_registry.create_requirements_service", return_value=mock_requirements_service)
    mocker.patch("amt.services.task_registry.create_measures_service", return_value=mock_measures_service)
    mocker.patch("amt.services.task_registry.is_requirement_applicable", return_value=True)

    mock_requirements_service.fetch_requirements.return_value = [
        Requirement(
            name="requirement",
            urn="urn:requirement:1",
            description="description",
            schema_version="1.1.0",
            links=["urn:measure:1", "urn:measure:2"],
            always_applicable=0,
            ai_act_profile=[
                RequirementAiActProfile(
                    type=[],
                    risk_category=[],
                    role=[],
                    open_source=[],
                    systemic_risk=[],
                    transparency_obligations=[],
                ),
            ],
        ),
    ]

    mock_measures_service.fetch_measures.side_effect = [
        [Measure(name="name 1", urn="measure:urn:1", description="", url="", schema_version="1.1.0")],
        [Measure(name="name 2", urn="measure:urn:2", description="", url="", schema_version="1.1.0")],
    ]

    ai_act_profile = AiActProfile()

    requirements, measures = await get_requirements_and_measures(ai_act_profile)

    assert len(requirements) == 1
    assert requirements[0].urn == "urn:requirement:1"

    assert len(measures) == 2
    assert {measure.urn for measure in measures} == {"urn:measure:1", "urn:measure:2"}


@pytest.mark.asyncio
async def test_get_requirements_and_measures_duplicate_measure_urns(mocker: MockerFixture):
    mock_requirements_service = mocker.AsyncMock()
    mock_measures_service = mocker.AsyncMock()

    mocker.patch("amt.services.task_registry.create_requirements_service", return_value=mock_requirements_service)
    mocker.patch("amt.services.task_registry.create_measures_service", return_value=mock_measures_service)
    mocker.patch("amt.services.task_registry.is_requirement_applicable", return_value=True)

    mock_requirements_service.fetch_requirements.return_value = [
        Requirement(
            name="requirement",
            urn="urn:requirement:1",
            description="description",
            schema_version="1.1.0",
            links=["urn:measure:1", "urn:measure:2"],
            always_applicable=0,
            ai_act_profile=[
                RequirementAiActProfile(
                    type=[],
                    risk_category=[],
                    role=[],
                    open_source=[],
                    systemic_risk=[],
                    transparency_obligations=[],
                ),
            ],
        ),
        Requirement(
            name="requirement",
            urn="urn:requirement:2",
            description="description",
            schema_version="1.1.0",
            links=["urn:measure:1", "urn:measure:3"],
            always_applicable=0,
            ai_act_profile=[
                RequirementAiActProfile(
                    type=[],
                    risk_category=[],
                    role=[],
                    open_source=[],
                    systemic_risk=[],
                    transparency_obligations=[],
                ),
            ],
        ),
    ]

    mock_measures_service.fetch_measures.side_effect = [
        [Measure(name="name 1", urn="measure:urn:1", description="", url="", schema_version="1.1.0")],
        [Measure(name="name 2", urn="measure:urn:2", description="", url="", schema_version="1.1.0")],
        [Measure(name="name 3", urn="measure:urn:3", description="", url="", schema_version="1.1.0")],
    ]

    ai_act_profile = AiActProfile()

    requirements, measures = await get_requirements_and_measures(ai_act_profile)

    assert len(requirements) == 2
    assert {requirement.urn for requirement in requirements} == {"urn:requirement:1", "urn:requirement:2"}

    assert len(measures) == 3
    assert {measure.urn for measure in measures} == {"urn:measure:1", "urn:measure:2", "urn:measure:3"}
