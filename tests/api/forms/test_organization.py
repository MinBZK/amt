from gettext import NullTranslations
from typing import cast
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from amt.api.forms.organization import get_organization_form
from amt.models import Organization, User
from amt.schema.webform import WebForm, WebFormField, WebFormSearchField
from amt.schema.webform_classes import WebFormFieldType
from fastapi import Request
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_get_organization_form_with_user_and_organization(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_translations = MagicMock(spec=NullTranslations)
    mock_translations.gettext.return_value = "translated"

    mock_user = MagicMock(spec=User)
    mock_organization = MagicMock(spec=Organization)
    mock_organization.id = UUID("12345678-1234-5678-1234-567812345678")

    # Setup mocks
    mock_editable = {"user_id": str(uuid4()), "role_id": 123, "type": "Organization"}

    # Patch the create_editable_for_role function to return mock_editable directly
    mocker.patch("amt.api.forms.organization.create_editable_for_role", return_value=mock_editable)

    # when
    form = await get_organization_form("form-id", mock_request, mock_translations, mock_user, mock_organization)

    # then
    assert isinstance(form, WebForm)
    assert form.id == "form-id"
    assert form.post_url == "/organizations/new"

    # Check if fields are created correctly
    assert len(form.fields) == 4

    # Verify the search URL includes the organization ID
    search_field = next((f for f in form.fields if isinstance(f, WebFormSearchField)), None)
    assert search_field is not None
    assert f"organization_id={mock_organization.id}" in search_field.search_url
    assert search_field.default_value == mock_editable


@pytest.mark.asyncio
async def test_get_organization_form_without_user() -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_translations = MagicMock(spec=NullTranslations)
    mock_translations.gettext.return_value = "translated"

    mock_organization = MagicMock(spec=Organization)
    mock_organization.id = UUID("12345678-1234-5678-1234-567812345678")

    # when
    form = await get_organization_form("form-id", mock_request, mock_translations, None, mock_organization)

    # then
    assert isinstance(form, WebForm)
    assert form.id == "form-id"

    # Check that fields are created correctly
    assert len(form.fields) == 4

    # Verify the default role is None when user is None
    search_field = next((f for f in form.fields if isinstance(f, WebFormSearchField)), None)
    assert search_field is not None
    assert search_field.default_value is None


@pytest.mark.asyncio
async def test_get_organization_form_without_organization(mocker: MockerFixture) -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_translations = MagicMock(spec=NullTranslations)
    mock_translations.gettext.return_value = "translated"

    mock_user = MagicMock(spec=User)

    # Setup mocks
    mock_editable = {"user_id": str(uuid4()), "role_id": 123, "type": "Organization"}

    # Patch the create_editable_for_role function to return mock_editable directly
    mocker.patch("amt.api.forms.organization.create_editable_for_role", return_value=mock_editable)

    # when
    form = await get_organization_form("form-id", mock_request, mock_translations, mock_user, None)

    # then
    assert isinstance(form, WebForm)

    # Check search URL doesn't include organization_id
    search_field = next((f for f in form.fields if isinstance(f, WebFormSearchField)), None)
    assert search_field is not None
    assert "organization_id" not in search_field.search_url
    assert search_field.default_value == mock_editable


@pytest.mark.asyncio
async def test_get_organization_form_field_properties() -> None:
    # given
    mock_request = MagicMock(spec=Request)
    mock_translations = MagicMock(spec=NullTranslations)
    mock_translations.gettext.return_value = "translated"

    # when
    form = await get_organization_form("form-id", mock_request, mock_translations, None, None)

    # then
    assert isinstance(form, WebForm)

    # Check specific field properties
    name_field = next((f for f in form.fields if f and hasattr(f, "name") and f.name == "name"), None)
    assert name_field is not None
    assert name_field.type == WebFormFieldType.TEXT
    # Need to cast to WebFormField to access these attributes
    field = cast(WebFormField, name_field)
    assert field.required
    assert field.attributes is not None
    assert "onkeyup" in field.attributes

    slug_field = next((f for f in form.fields if f and hasattr(f, "name") and f.name == "slug"), None)
    assert slug_field is not None
    assert slug_field.type == WebFormFieldType.TEXT
    field = cast(WebFormField, slug_field)
    assert field.required

    submit_button = next((f for f in form.fields if f and hasattr(f, "name") and f.name == "submit"), None)
    assert submit_button is not None
