import pytest
from amt.api.ai_act_profile import AiActProfileSelector, SelectAiProfileItem
from amt.api.editable_value_providers import AIActValuesProvider, RolesValuesProvider
from amt.core.authorization import AuthorizationType
from amt.schema.webform_classes import WebFormOption
from pytest_mock import MockerFixture

from tests.constants import default_fastapi_request


@pytest.mark.asyncio
async def test_roles_values_provider_organization(mocker: MockerFixture):
    # Given
    provider = RolesValuesProvider()
    request = default_fastapi_request()
    request.state.authorization_type = AuthorizationType.ORGANIZATION

    # When
    result = await provider.get_values(request)

    # Then
    assert len(result) == 3
    assert isinstance(result[0], WebFormOption)
    assert [option.value for option in result] == ["1", "2", "3"]
    assert [option.display_value for option in result] == [
        "Organization Maintainer",
        "Organization Member",
        "Organization Viewer",
    ]


@pytest.mark.asyncio
async def test_roles_values_provider_algorithm(mocker: MockerFixture):
    # Given
    provider = RolesValuesProvider()
    request = default_fastapi_request()
    request.state.authorization_type = AuthorizationType.ALGORITHM

    # When
    result = await provider.get_values(request)

    # Then
    assert len(result) == 3
    assert isinstance(result[0], WebFormOption)
    assert [option.value for option in result] == ["4", "5", "6"]
    assert [option.display_value for option in result] == [
        "Algorithm Maintainer",
        "Algorithm Member",
        "Algorithm Viewer",
    ]


@pytest.mark.asyncio
async def test_roles_values_provider_no_auth_type(mocker: MockerFixture):
    # Given
    provider = RolesValuesProvider()
    request = default_fastapi_request()
    request.state.authorization_type = None

    # When
    result = await provider.get_values(request)

    # Then
    assert len(result) == 0


@pytest.mark.asyncio
async def test_ai_act_values_provider_with_matching_target(mocker: MockerFixture):
    # Given
    provider = AIActValuesProvider(type="type")
    request = default_fastapi_request()

    # Create a mock profile with options
    profile_selector = AiActProfileSelector()
    profile_selector.dropdown_select = [
        SelectAiProfileItem(
            item=mocker.MagicMock(), options=["option1", "option2", "option3"], translations=mocker.MagicMock()
        )
    ]
    profile_selector.dropdown_select[0].target_name = "type"

    mocker.patch("amt.api.editable_value_providers.get_ai_act_profile_selector", return_value=profile_selector)

    # When
    result = await provider.get_values(request)

    # Then
    assert len(result) == 3
    assert isinstance(result[0], WebFormOption)
    assert [option.value for option in result] == ["option1", "option2", "option3"]
    assert [option.display_value for option in result] == ["option1", "option2", "option3"]


@pytest.mark.asyncio
async def test_ai_act_values_provider_with_multiple_select_options(mocker: MockerFixture):
    # Given
    provider = AIActValuesProvider(type="role")
    request = default_fastapi_request()

    # Create a mock profile with options in multiple_select
    profile_selector = AiActProfileSelector()
    profile_selector.dropdown_select = []
    profile_selector.multiple_select = [
        SelectAiProfileItem(item=mocker.MagicMock(), options=["role1", "role2"], translations=mocker.MagicMock())
    ]
    profile_selector.multiple_select[0].target_name = "role"

    mocker.patch("amt.api.editable_value_providers.get_ai_act_profile_selector", return_value=profile_selector)

    # When
    result = await provider.get_values(request)

    # Then
    assert len(result) == 2
    assert isinstance(result[0], WebFormOption)
    assert [option.value for option in result] == ["role1", "role2"]
    assert [option.display_value for option in result] == ["role1", "role2"]


@pytest.mark.asyncio
async def test_ai_act_values_provider_with_no_matching_target(mocker: MockerFixture):
    # Given
    provider = AIActValuesProvider(type="nonexistent_type")
    request = default_fastapi_request()

    # Create a mock profile with options
    profile_selector = AiActProfileSelector()
    profile_selector.dropdown_select = [
        SelectAiProfileItem(
            item=mocker.MagicMock(), options=["option1", "option2", "option3"], translations=mocker.MagicMock()
        )
    ]
    profile_selector.dropdown_select[0].target_name = "type"
    profile_selector.multiple_select = []

    mocker.patch("amt.api.editable_value_providers.get_ai_act_profile_selector", return_value=profile_selector)

    # When
    result = await provider.get_values(request)

    # Then
    assert len(result) == 0


@pytest.mark.asyncio
async def test_ai_act_values_provider_with_none_options(mocker: MockerFixture):
    # Given
    provider = AIActValuesProvider(type="type")
    request = default_fastapi_request()

    # Create a mock profile with None options
    profile_selector = AiActProfileSelector()
    profile_selector.dropdown_select = [
        SelectAiProfileItem(item=mocker.MagicMock(), options=[], translations=mocker.MagicMock())
    ]
    profile_selector.dropdown_select[0].target_name = "type"
    profile_selector.dropdown_select[0].options = None
    profile_selector.multiple_select = []

    mocker.patch("amt.api.editable_value_providers.get_ai_act_profile_selector", return_value=profile_selector)

    # When
    result = await provider.get_values(request)

    # Then
    assert len(result) == 0
