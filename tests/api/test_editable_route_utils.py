from unittest.mock import AsyncMock, MagicMock

import pytest
from amt.api.editable_classes import EditModes, ResolvedEditable
from amt.api.editable_route_utils import create_editable_for_role, get_user_id_or_error, update_handler
from amt.core.authorization import AuthorizationType
from amt.core.exceptions import AMTError
from amt.models import User
from amt.schema.webform_classes import WebFormOption
from fastapi import Request
from fastapi.templating import Jinja2Templates
from pytest_mock import MockerFixture
from starlette.responses import HTMLResponse


@pytest.mark.asyncio
async def test_get_user_id_or_error_valid_user(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_user = {"sub": "test-user-id"}
    mocker.patch("amt.api.editable_route_utils.get_user", return_value=mock_user)

    # when
    user_id = get_user_id_or_error(mock_request)

    # then
    assert user_id == "test-user-id"


@pytest.mark.asyncio
async def test_get_user_id_or_error_no_user(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mocker.patch("amt.api.editable_route_utils.get_user", return_value=None)

    # when/then
    with pytest.raises(AMTError):
        get_user_id_or_error(mock_request)


@pytest.mark.asyncio
async def test_get_user_id_or_error_no_sub(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_user = {"name": "Test User"}  # No 'sub' field
    mocker.patch("amt.api.editable_route_utils.get_user", return_value=mock_user)

    # when/then
    with pytest.raises(AMTError):
        get_user_id_or_error(mock_request)


@pytest.mark.asyncio
async def test_create_editable_for_role(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_request.state = MagicMock()

    mock_services_provider = MagicMock()

    mock_user = MagicMock(spec=User)
    mock_user.id = "user-123"
    mock_user.name = "Test User"

    auth_type = AuthorizationType.ORGANIZATION
    type_id = 456
    role_id = 789

    mocker.patch("amt.api.editable_route_utils.get_user_id_or_error", return_value="test-user-id")

    mock_resolved_editable = MagicMock(spec=ResolvedEditable)
    mocker.patch("amt.api.editable_route_utils.get_resolved_editable", return_value=mock_resolved_editable)

    mock_enriched_editable = MagicMock(spec=ResolvedEditable)
    mock_enrich = mocker.patch("amt.api.editable_route_utils.enrich_editable", return_value=mock_enriched_editable)

    # when
    result = await create_editable_for_role(
        mock_request, mock_services_provider, mock_user, auth_type, type_id, role_id
    )

    # then
    assert result == mock_enriched_editable
    assert mock_request.state.authorization_type == auth_type

    # Verify enrich_editable was called with correct parameters
    mock_enrich.assert_called_once()
    call_args = mock_enrich.call_args[0]
    assert call_args[0] == mock_resolved_editable
    assert call_args[1] == EditModes.EDIT
    assert call_args[2] == {"user_id": "test-user-id"}
    assert call_args[3] == mock_services_provider
    assert call_args[4] == mock_request

    # Check resource object was properly created
    resource_object = mock_enrich.call_args[1]["resource_object"]
    assert isinstance(resource_object["user_id"], WebFormOption)
    assert resource_object["user_id"].value == "user-123"
    assert resource_object["user_id"].display_value == "Test User"
    assert resource_object["role_id"] == role_id
    assert resource_object["type"] == "Organization"
    assert resource_object["type_id"] == type_id


@pytest.mark.asyncio
async def test_update_handler_validation_state(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_request.json = AsyncMock(return_value={"field": "value"})

    mock_services_provider = MagicMock()
    mock_templates = MagicMock(spec=Jinja2Templates)
    mocker.patch("amt.api.editable_route_utils.templates", mock_templates)

    # Create a valid current state
    current_state_str = "VALIDATE"

    # Setup mocks for find_matching_editable
    mock_editable = MagicMock()
    mock_editable.has_hook = MagicMock(return_value=False)
    mock_editable.validate = AsyncMock()
    mock_editable.children = []
    mock_editable.couples = []
    mock_editable.converter = None
    mock_editable.relative_resource_path = "test/path"
    mock_editable.resource_object = {"id": 123}

    mocker.patch("amt.api.editable_route_utils.get_user_id_or_error", return_value="test-user-id")
    mocker.patch("amt.api.editable_route_utils.find_matching_editable", return_value=(MagicMock(), {}))
    mocker.patch("amt.api.editable_route_utils.get_resolved_editable", return_value=MagicMock())
    mocker.patch("amt.api.editable_route_utils.enrich_editable", return_value=mock_editable)
    mocker.patch("amt.api.editable_route_utils.save_editable", return_value=mock_editable)
    mocker.patch("amt.api.editable_route_utils.get_resolved_editables", return_value=[])

    mock_templates.TemplateResponse.return_value = HTMLResponse(content="test content")

    # when
    result = await update_handler(
        request=mock_request,
        full_resource_path="test/resource/path",
        base_href="/test/base",
        current_state_str=current_state_str,
        context_variables={},
        edit_mode=EditModes.EDIT,
        services_provider=mock_services_provider,
    )

    # then
    assert isinstance(result, HTMLResponse)
    assert mock_editable.validate.called
    mock_templates.TemplateResponse.assert_called_once()


@pytest.mark.asyncio
async def test_update_handler_with_hook(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_request.json = AsyncMock(return_value={"field": "value"})

    mock_services_provider = MagicMock()
    mock_templates = MagicMock(spec=Jinja2Templates)
    mocker.patch("amt.api.editable_route_utils.templates", mock_templates)

    # Create a valid current state that will trigger a hook
    current_state_str = "PRE_SAVE"

    # Setup mocks for editable with hook
    mock_editable = MagicMock()
    mock_editable.has_hook = MagicMock(return_value=True)
    mock_hook_response = HTMLResponse(content="hook response")
    mock_editable.run_hook = AsyncMock(return_value=mock_hook_response)

    mocker.patch("amt.api.editable_route_utils.get_user_id_or_error", return_value="test-user-id")
    mocker.patch("amt.api.editable_route_utils.find_matching_editable", return_value=(MagicMock(), {}))
    mocker.patch("amt.api.editable_route_utils.get_resolved_editable", return_value=MagicMock())
    mocker.patch("amt.api.editable_route_utils.enrich_editable", return_value=mock_editable)

    # when
    result = await update_handler(
        request=mock_request,
        full_resource_path="test/resource/path",
        base_href="/test/base",
        current_state_str=current_state_str,
        context_variables={},
        edit_mode=EditModes.EDIT,
        services_provider=mock_services_provider,
    )

    # then
    assert result == mock_hook_response
    assert mock_editable.run_hook.called
    # Template response should not be called as hook returns early
    assert not mock_templates.TemplateResponse.called


@pytest.mark.asyncio
async def test_update_handler_save_state_no_hook(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_request.json = AsyncMock(return_value={"field": "value"})

    mock_services_provider = MagicMock()
    mock_templates = MagicMock(spec=Jinja2Templates)
    mocker.patch("amt.api.editable_route_utils.templates", mock_templates)

    # Create a save state
    current_state_str = "SAVE"

    # Setup mocks
    mock_editable = MagicMock()
    mock_editable.has_hook = MagicMock(return_value=False)
    mock_editable.children = []
    mock_editable.couples = []
    mock_editable.converter = None
    mock_editable.relative_resource_path = "test/path"
    mock_editable.resource_object = {"id": 123}

    mocker.patch("amt.api.editable_route_utils.get_user_id_or_error", return_value="test-user-id")
    mocker.patch("amt.api.editable_route_utils.find_matching_editable", return_value=(MagicMock(), {}))
    mocker.patch("amt.api.editable_route_utils.get_resolved_editable", return_value=MagicMock())
    mocker.patch("amt.api.editable_route_utils.enrich_editable", return_value=mock_editable)
    mock_save = mocker.patch("amt.api.editable_route_utils.save_editable", return_value=mock_editable)
    mocker.patch("amt.api.editable_route_utils.get_resolved_editables", return_value=[])

    mock_templates.TemplateResponse.return_value = HTMLResponse(content="test content")

    # when
    result = await update_handler(
        request=mock_request,
        full_resource_path="test/resource/path",
        base_href="/test/base",
        current_state_str=current_state_str,
        context_variables={},
        edit_mode=EditModes.EDIT,
        services_provider=mock_services_provider,
    )

    # then
    assert isinstance(result, HTMLResponse)
    assert mock_save.called
    mock_templates.TemplateResponse.assert_called_once()


@pytest.mark.asyncio
async def test_update_handler_with_converter(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_request.json = AsyncMock(return_value={"field": "value"})

    mock_services_provider = MagicMock()
    mock_templates = MagicMock(spec=Jinja2Templates)
    mocker.patch("amt.api.editable_route_utils.templates", mock_templates)

    # Create a completed state
    current_state_str = "COMPLETED"

    # Setup mock converter
    mock_converter = MagicMock()
    mock_converter.view = AsyncMock(return_value="converted value")

    # Setup editable with converter
    mock_editable = MagicMock()
    mock_editable.has_hook = MagicMock(return_value=False)
    mock_editable.children = []
    mock_editable.couples = []
    mock_editable.converter = mock_converter
    mock_editable.value = "raw value"
    mock_editable.relative_resource_path = "test/path"
    mock_editable.resource_object = {"id": 123}

    mocker.patch("amt.api.editable_route_utils.get_user_id_or_error", return_value="test-user-id")
    mocker.patch("amt.api.editable_route_utils.find_matching_editable", return_value=(MagicMock(), {}))
    mocker.patch("amt.api.editable_route_utils.get_resolved_editable", return_value=MagicMock())
    mocker.patch("amt.api.editable_route_utils.enrich_editable", return_value=mock_editable)
    mocker.patch("amt.api.editable_route_utils.get_resolved_editables", return_value=[])

    mock_templates.TemplateResponse.return_value = HTMLResponse(content="test content")

    # when
    result = await update_handler(
        request=mock_request,
        full_resource_path="test/resource/path",
        base_href="/test/base",
        current_state_str=current_state_str,
        context_variables={},
        edit_mode=EditModes.EDIT,
        services_provider=mock_services_provider,
    )

    # then
    assert isinstance(result, HTMLResponse)
    mock_converter.view.assert_called_once()
    assert mock_editable.value == "converted value"
    mock_templates.TemplateResponse.assert_called_once()
