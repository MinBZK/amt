from unittest.mock import AsyncMock

import pytest
from amt.api import editable_converters
from amt.api.editable_classes import ResolvedEditable
from amt.api.lifecycles import Lifecycles
from amt.models import Organization, Role
from amt.services.services_provider import ServicesProvider
from pytest_mock import MockerFixture

from tests.constants import default_user


@pytest.mark.asyncio
async def test_editable_converter(mocker: MockerFixture):
    resolved_editable = mocker.Mock(spec=ResolvedEditable)

    editable_converter = editable_converters.EditableConverter()
    result = await editable_converter.read(
        in_value="test",
        request=None,
        editable=resolved_editable,
        editable_context={},
        services_provider=None,
    )
    assert result.value == "test"

    result = await editable_converter.write(
        in_value="test",
        request=None,
        editable=resolved_editable,
        editable_context={},
        services_provider=None,
    )
    assert result.value == "test"

    result = await editable_converter.view(
        in_value="test",
        request=None,
        editable=resolved_editable,
        editable_context={},
        services_provider=None,
    )
    assert result.value == "test"


@pytest.mark.asyncio
async def test_editable_converter_for_organization_in_algorithm(mocker: MockerFixture):
    # Given
    editable_converter = editable_converters.EditableConverterForOrganizationInAlgorithm()
    organization: Organization = Organization(id=1, name="test organization name")

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_organization_service = AsyncMock()
    mock_organization_service.find_by_id_and_user_id.return_value = organization
    services_provider.get.return_value = mock_organization_service

    resolved_editable = mocker.Mock(spec=ResolvedEditable)

    editable_context = {"user_id": default_user().id}

    # When - test read method
    result = await editable_converter.read(
        in_value=organization,
        request=None,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == "1"
    assert result.display_value == "test organization name"

    # When - test write method
    result = await editable_converter.write(
        in_value="1",
        request=None,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == organization
    mock_organization_service.find_by_id_and_user_id.assert_called_once_with(
        organization_id=1, user_id=default_user().id
    )

    # When - test view method
    result = await editable_converter.view(
        in_value=organization,
        request=None,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == "1"
    assert result.display_value == "test organization name"


@pytest.mark.asyncio
async def test_editable_converter_for_organization_in_algorithm_missing_services_provider(mocker: MockerFixture):
    # Given
    editable_converter = editable_converters.EditableConverterForOrganizationInAlgorithm()
    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    editable_context = {"user_id": default_user().id}

    # When/Then - test write method with missing services provider
    with pytest.raises(TypeError, match="Services provider must be provided"):
        await editable_converter.write(
            in_value="1",
            request=None,
            editable=resolved_editable,
            editable_context=editable_context,
            services_provider=None,
        )


@pytest.mark.asyncio
async def test_editable_converter_for_authorization_role(mocker: MockerFixture):
    # Given
    editable_converter = editable_converters.EditableConverterForAuthorizationRole()
    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    role_id = 1
    role = Role(id=role_id, name="Admin Role")

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_auth_service = AsyncMock()
    mock_auth_service.get_role_by_id.return_value = role
    services_provider.get.return_value = mock_auth_service

    editable_context = {"user_id": default_user().id}

    # Mock request and translations
    mock_request = mocker.Mock()
    mock_translations = mocker.Mock()
    mock_translations.gettext.return_value = "Admin Role"
    mocker.patch("amt.core.dynamic_translations.get_current_translation", return_value=mock_translations)

    # When - test view method
    result = await editable_converter.view(
        in_value=role_id,
        request=mock_request,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == role_id
    assert result.display_value == "Admin Role"
    mock_auth_service.get_role_by_id.assert_called_once_with(role_id)

    # Reset mock
    mock_auth_service.get_role_by_id.reset_mock()

    # When - test write method
    result = await editable_converter.write(
        in_value=role_id,
        request=mock_request,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == role_id
    assert result.display_value == "Admin Role"
    mock_auth_service.get_role_by_id.assert_called_once_with(role_id)


@pytest.mark.asyncio
async def test_editable_converter_for_authorization_role_unknown_role(mocker: MockerFixture):
    # Given
    editable_converter = editable_converters.EditableConverterForAuthorizationRole()
    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    role_id = 99  # Non-existent role ID

    services_provider = mocker.Mock(spec=ServicesProvider)
    mock_auth_service = AsyncMock()
    mock_auth_service.get_role_by_id.return_value = None  # Role not found
    services_provider.get.return_value = mock_auth_service

    editable_context = {"user_id": default_user().id}

    # Mock request and translations
    mock_request = mocker.Mock()
    mock_translations = mocker.Mock()
    mock_translations.gettext.return_value = "Unknown"
    mocker.patch("amt.core.dynamic_translations.get_current_translation", return_value=mock_translations)

    # When - test view method with unknown role
    result = await editable_converter.view(
        in_value=role_id,
        request=mock_request,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == role_id
    assert result.display_value == "Unknown"
    mock_auth_service.get_role_by_id.assert_called_once_with(role_id)


@pytest.mark.asyncio
async def test_editable_converter_for_authorization_role_no_services_provider(mocker: MockerFixture):
    # Given
    editable_converter = editable_converters.EditableConverterForAuthorizationRole()
    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    role_id = 1

    editable_context = {"user_id": default_user().id}

    # Mock request
    mock_request = mocker.Mock()

    # When/Then - test with missing services provider
    with pytest.raises(TypeError, match="Services provider must be provided"):
        await editable_converter.view(
            in_value=role_id,
            request=mock_request,
            editable=resolved_editable,
            editable_context=editable_context,
            services_provider=None,
        )

    # When/Then - test write method with missing services provider
    with pytest.raises(TypeError, match="Services provider must be provided"):
        await editable_converter.write(
            in_value=role_id,
            request=mock_request,
            editable=resolved_editable,
            editable_context=editable_context,
            services_provider=None,
        )


@pytest.mark.asyncio
async def test_editable_status_converter_for_systemcard(mocker: MockerFixture):
    # Given
    editable_converter = editable_converters.StatusConverterForSystemcard()
    resolved_editable = mocker.Mock(spec=ResolvedEditable)
    editable_context = {"user_id": default_user().id}
    services_provider = mocker.Mock(spec=ServicesProvider)

    # When - test read method with exact case match
    result = await editable_converter.read(
        in_value="Organisatieverantwoordelijkheden",
        request=None,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES.value
    assert result.display_value == Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES.name

    # When - test read method with case-insensitive match
    result = await editable_converter.read(
        in_value="organisatieverantwoordelijkheden",  # lowercase
        request=None,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES.value
    assert result.display_value == Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES.name

    # When - test read method with non-matching value
    result = await editable_converter.read(
        in_value="Non-existent Phase",
        request=None,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == "Non-existent Phase"
    assert result.display_value == "Non-existent Phase"

    # When - test write method
    result = await editable_converter.write(
        in_value=Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES.value,
        request=None,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == "Organisatieverantwoordelijkheden"
    assert result.display_value == Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES.value

    # When - test write method with unknown value
    result = await editable_converter.write(
        in_value="unknown-lifecycle",
        request=None,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == "Unknown"
    assert result.display_value == "unknown-lifecycle"

    # When - test view method (uses default implementation)
    result = await editable_converter.view(
        in_value="Dataverkenning en datapreparatie",
        request=None,
        editable=resolved_editable,
        editable_context=editable_context,
        services_provider=services_provider,
    )

    # Then
    assert result.value == "Dataverkenning en datapreparatie"
