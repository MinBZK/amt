from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from amt.api.editable_classes import EditableValidator, EditModes, ResolvedEditable
from amt.api.editable_enforcers import (
    EditableEnforcerForOrganizationInAlgorithm,
    EditableEnforcerMustHaveMaintainer,
    EditableEnforcerMustHaveMaintainerForLists,
)
from amt.core.exceptions import AMTAuthorizationError, AMTRepositoryError
from amt.models import Authorization, Organization
from amt.models.authorization import Authorization as AuthorizationModel
from amt.services.services_provider import ServicesProvider
from fastapi.exceptions import RequestValidationError
from pytest_mock import MockerFixture

from tests.constants import default_fastapi_request


@pytest.mark.asyncio
async def test_editable_enforcer_for_organization_in_algorithm(mocker: MockerFixture):
    # given
    editable_enforcer = EditableEnforcerForOrganizationInAlgorithm()
    organization: Organization = Organization(id=1, name="test organization name")

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_organization_service = AsyncMock()
    mock_organization_service.find_by_id_and_user_id.return_value = organization
    services_provider.get.return_value = mock_organization_service

    resolved_editable = mocker.Mock(spec=ResolvedEditable)

    context = {"user_id": 1, "new_values": {"organization": 2}}

    # when/then
    try:
        await editable_enforcer.enforce(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context=context,
            edit_mode=EditModes.EDIT,
            services_provider=services_provider,
        )
    except AMTAuthorizationError:
        pytest.fail("Unexpected exception raised")

    # when/then - test authorization error case
    mock_organization_service.find_by_id_and_user_id.side_effect = AMTRepositoryError("Not found")
    with pytest.raises(AMTAuthorizationError):
        await editable_enforcer.enforce(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context=context,
            edit_mode=EditModes.EDIT,
            services_provider=services_provider,
        )


@pytest.mark.asyncio
async def test_editable_enforcer_must_have_maintainer_organization(mocker: MockerFixture):
    # given
    editable_enforcer = EditableEnforcerMustHaveMaintainer()

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_auth_service = AsyncMock()

    mock_role = AsyncMock()
    mock_role.id = 5
    mock_auth_service.get_role.return_value = mock_role

    # Authorization with multiple maintainers
    # Use UUIDs for all user IDs as specified in the model
    auth_list = [
        (None, AuthorizationModel(user_id=UUID("11111111-1111-1111-1111-111111111111"), role_id=5), None, None),
        (None, AuthorizationModel(user_id=UUID("22222222-2222-2222-2222-222222222222"), role_id=5), None, None),
    ]
    mock_auth_service.find_all.return_value = auth_list
    services_provider.get.return_value = mock_auth_service

    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    mock_authorization = AsyncMock(spec=Authorization)
    mock_authorization.user_id = UUID("11111111-1111-1111-1111-111111111111")
    resolved_editable.get_resource_object.return_value = mock_authorization

    context = {"organization_id": 1, "new_values": {"role": "3"}}

    # when/then - with multiple maintainers, should allow changing role
    await editable_enforcer.enforce(
        request=default_fastapi_request(),
        editable=resolved_editable,
        editable_context=context,
        edit_mode=EditModes.EDIT,
        services_provider=services_provider,
    )

    # given - with only one maintainer, should not allow changing that maintainer's role
    auth_list = [
        (None, AuthorizationModel(user_id=UUID("11111111-1111-1111-1111-111111111111"), role_id=5), None, None)
    ]
    mock_auth_service.find_all.return_value = auth_list

    # when/then - should raise exception when trying to change the only maintainer's role
    with pytest.raises(RequestValidationError) as e:
        await editable_enforcer.enforce(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context=context,
            edit_mode=EditModes.EDIT,
            services_provider=services_provider,
        )
    assert e.value.args[0][0]["type"] == "maintainer_role_required_with_context"


@pytest.mark.asyncio
async def test_editable_enforcer_must_have_maintainer_algorithm(mocker: MockerFixture):
    # given
    editable_enforcer = EditableEnforcerMustHaveMaintainer()

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_auth_service = AsyncMock()

    mock_role = AsyncMock()
    mock_role.id = 7
    mock_auth_service.get_role.return_value = mock_role

    auth_list = [
        (None, AuthorizationModel(user_id=UUID("11111111-1111-1111-1111-111111111111"), role_id=7), None, None),
        (None, AuthorizationModel(user_id=UUID("22222222-2222-2222-2222-222222222222"), role_id=7), None, None),
    ]
    mock_auth_service.find_all.return_value = auth_list
    services_provider.get.return_value = mock_auth_service

    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    mock_authorization = AsyncMock(spec=Authorization)
    mock_authorization.user_id = UUID("11111111-1111-1111-1111-111111111111")
    resolved_editable.get_resource_object.return_value = mock_authorization

    context = {"algorithm_id": 1, "new_values": {"role": "3"}}

    # when/then - with multiple maintainers, should allow changing role
    await editable_enforcer.enforce(
        request=default_fastapi_request(),
        editable=resolved_editable,
        editable_context=context,
        edit_mode=EditModes.EDIT,
        services_provider=services_provider,
    )


@pytest.mark.asyncio
async def test_editable_enforcer_must_have_maintainer_delete_mode(mocker: MockerFixture):
    # given
    editable_enforcer = EditableEnforcerMustHaveMaintainer()

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_auth_service = AsyncMock()

    mock_role = AsyncMock()
    mock_role.id = 5
    mock_auth_service.get_role.return_value = mock_role

    auth_list = [
        (None, AuthorizationModel(user_id=UUID("11111111-1111-1111-1111-111111111111"), role_id=5), None, None)
    ]
    mock_auth_service.find_all.return_value = auth_list
    services_provider.get.return_value = mock_auth_service

    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    mock_authorization = AsyncMock(spec=Authorization)
    mock_authorization.user_id = UUID("11111111-1111-1111-1111-111111111111")
    resolved_editable.get_resource_object.return_value = mock_authorization

    context = {"organization_id": 1, "new_values": {"role": "3"}}

    # when/then - in DELETE mode, should check maintainer requirement
    with pytest.raises(RequestValidationError):
        await editable_enforcer.enforce(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context=context,
            edit_mode=EditModes.DELETE,
            services_provider=services_provider,
        )


@pytest.mark.asyncio
async def test_editable_enforcer_must_have_maintainer_for_lists_organization(mocker: MockerFixture):
    # given
    editable_enforcer = EditableEnforcerMustHaveMaintainerForLists()

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_auth_service = AsyncMock()

    mock_role = AsyncMock()
    mock_role.id = 5
    mock_auth_service.get_role.return_value = mock_role
    services_provider.get.return_value = mock_auth_service

    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    resolved_editable.safe_html_path.return_value = "authorization"
    resolved_editable.last_path_item.return_value = "authorization"

    # Valid case: has at least one maintainer in the new values
    context_with_maintainer = {
        "new_values": {
            "authorization": [
                {
                    "type": "Organization",
                    "type_id": "1",
                    "user_id": "11111111-1111-1111-1111-111111111111",
                    "role_id": "5",
                },
                {
                    "type": "Organization",
                    "type_id": "1",
                    "user_id": "22222222-2222-2222-2222-222222222222",
                    "role_id": "3",
                },
            ]
        }
    }

    # when/then - should pass with a maintainer included
    with patch.object(
        EditableValidator, "get_new_value", return_value=context_with_maintainer["new_values"]["authorization"]
    ):
        await editable_enforcer.enforce(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context=context_with_maintainer,
            edit_mode=EditModes.EDIT,
            services_provider=services_provider,
        )

    # given - case without maintainer but existing maintainer stays
    context_no_maintainer = {
        "new_values": {
            "authorization": [
                {
                    "type": "Organization",
                    "type_id": "1",
                    "user_id": "33333333-3333-3333-3333-333333333333",
                    "role_id": "3",
                },
                {
                    "type": "Organization",
                    "type_id": "1",
                    "user_id": "44444444-4444-4444-4444-444444444444",
                    "role_id": "3",
                },
            ]
        }
    }

    auth_list = [
        (None, AuthorizationModel(user_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), role_id=5), None, None)
    ]
    mock_auth_service.find_all.return_value = auth_list

    # when/then - with existing maintainer who stays, should pass
    with patch.object(
        EditableValidator, "get_new_value", return_value=context_no_maintainer["new_values"]["authorization"]
    ):
        await editable_enforcer.enforce(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context=context_no_maintainer,
            edit_mode=EditModes.SAVE_NEW,
            services_provider=services_provider,
        )

    # given - case without maintainer and no existing maintainer remains
    auth_list = [
        (None, AuthorizationModel(user_id=UUID("33333333-3333-3333-3333-333333333333"), role_id=5), None, None)
    ]
    mock_auth_service.find_all.return_value = auth_list

    # when/then - should fail when removing all maintainers
    with patch.object(
        EditableValidator, "get_new_value", return_value=context_no_maintainer["new_values"]["authorization"]
    ):
        with pytest.raises(RequestValidationError) as e:
            await editable_enforcer.enforce(
                request=default_fastapi_request(),
                editable=resolved_editable,
                editable_context=context_no_maintainer,
                edit_mode=EditModes.EDIT,
                services_provider=services_provider,
            )
        assert e.value.args[0][0]["type"] == "maintainer_role_required"


@pytest.mark.asyncio
async def test_editable_enforcer_must_have_maintainer_for_lists_algorithm(mocker: MockerFixture):
    # given
    editable_enforcer = EditableEnforcerMustHaveMaintainerForLists()

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_auth_service = AsyncMock()

    mock_role = AsyncMock()
    mock_role.id = 7
    mock_auth_service.get_role.return_value = mock_role
    services_provider.get.return_value = mock_auth_service

    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    resolved_editable.safe_html_path.return_value = "authorization"
    resolved_editable.last_path_item.return_value = "authorization"

    # Valid case: has at least one maintainer in the new values
    context_with_maintainer = {
        "new_values": {
            "authorization": [
                {
                    "type": "Algorithm",
                    "type_id": "1",
                    "user_id": "11111111-1111-1111-1111-111111111111",
                    "role_id": "7",
                },
                {
                    "type": "Algorithm",
                    "type_id": "1",
                    "user_id": "22222222-2222-2222-2222-222222222222",
                    "role_id": "3",
                },
            ]
        }
    }

    # when/then - should pass with a maintainer included
    with patch.object(
        EditableValidator, "get_new_value", return_value=context_with_maintainer["new_values"]["authorization"]
    ):
        await editable_enforcer.enforce(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context=context_with_maintainer,
            edit_mode=EditModes.EDIT,
            services_provider=services_provider,
        )


@pytest.mark.asyncio
async def test_editable_enforcer_must_have_maintainer_for_lists_unknown_type(mocker: MockerFixture):
    # given
    editable_enforcer = EditableEnforcerMustHaveMaintainerForLists()

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_auth_service = AsyncMock()
    services_provider.get.return_value = mock_auth_service

    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    resolved_editable.last_path_item.return_value = "authorization"

    # Invalid authorization type - will raise ValueError in the AuthorizationType constructor
    invalid_auth_list = [
        {"type": "Unknown", "type_id": "1", "user_id": "1", "role_id": "5"},
    ]

    # when/then - should raise ValueError for invalid enum value
    with (
        patch.object(EditableValidator, "get_new_value", return_value=invalid_auth_list),
        pytest.raises(ValueError, match="'Unknown' is not a valid AuthorizationType"),
    ):
        await editable_enforcer.enforce(
            request=default_fastapi_request(),
            editable=resolved_editable,
            editable_context={},
            edit_mode=EditModes.EDIT,
            services_provider=services_provider,
        )


@pytest.mark.asyncio
async def test_editable_enforcer_must_have_maintainer_for_lists_no_type_id(mocker: MockerFixture):
    # given
    editable_enforcer = EditableEnforcerMustHaveMaintainerForLists()

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_auth_service = AsyncMock()

    mock_role = AsyncMock()
    mock_role.id = 5
    mock_auth_service.get_role.return_value = mock_role
    services_provider.get.return_value = mock_auth_service

    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    resolved_editable.safe_html_path.return_value = "authorization"
    resolved_editable.last_path_item.return_value = "authorization"

    # Case with no maintainer and no type_id
    auth_list_no_type_id = [
        {"type": "Organization", "user_id": "33333333-3333-3333-3333-333333333333", "role_id": "3"},
        {"type": "Organization", "user_id": "44444444-4444-4444-4444-444444444444", "role_id": "3"},
    ]

    # when/then - should fail when no maintainer and no type_id
    with patch.object(EditableValidator, "get_new_value", return_value=auth_list_no_type_id):
        with pytest.raises(RequestValidationError) as e:
            await editable_enforcer.enforce(
                request=default_fastapi_request(),
                editable=resolved_editable,
                editable_context={},
                edit_mode=EditModes.EDIT,
                services_provider=services_provider,
            )
        assert e.value.args[0][0]["type"] == "maintainer_role_required"
