from gettext import NullTranslations
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from amt.api.forms.algorithm import get_algorithm_form, get_algorithm_members_form, get_organization_select_field
from amt.core.authorization import AuthorizationVerb
from amt.models.algorithm import Algorithm
from amt.models.organization import Organization
from amt.schema.webform import WebForm, WebFormField
from amt.schema.webform_classes import WebFormFieldType, WebFormOption
from amt.services.organizations import OrganizationsService
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_get_organization_select_field(mocker: MockerFixture) -> None:
    # given
    _ = MagicMock()
    _.return_value = "Translated Text"

    organization_id = 1
    user_id = UUID("11111111-1111-1111-1111-111111111111")
    permissions = {
        "organization/1/algorithm": [AuthorizationVerb.CREATE],
        "organization/2/algorithm": [AuthorizationVerb.CREATE],
    }

    org1 = Organization(id=1, name="Org 1", slug="org-1", created_by_id=user_id)
    org2 = Organization(id=2, name="Org 2", slug="org-2", created_by_id=user_id)

    organizations_service = mocker.Mock(spec=OrganizationsService)
    organizations_service.get_organizations_for_user = AsyncMock(return_value=[org1, org2])

    # when
    result = await get_organization_select_field(_, organization_id, organizations_service, user_id, permissions)

    # then
    assert isinstance(result, WebFormField)
    assert result.type == WebFormFieldType.SELECT
    assert result.name == "organization_id"
    assert result.default_value == "1"
    assert len(result.options) == 3  # select option + 2 orgs  # pyright: ignore[reportArgumentType]
    assert result.options[0].value == ""  # pyright: ignore[reportOptionalSubscript, reportUnknownMemberType]
    assert result.options[1].value == "1"  # pyright: ignore[reportOptionalSubscript, reportUnknownMemberType]
    assert result.options[1].display_value == "Org 1"  # pyright: ignore[reportOptionalSubscript, reportUnknownMemberType]
    assert result.options[2].value == "2"  # pyright: ignore[reportOptionalSubscript, reportUnknownMemberType]
    assert result.options[2].display_value == "Org 2"  # pyright: ignore[reportOptionalSubscript, reportUnknownMemberType]


@pytest.mark.asyncio
async def test_get_algorithm_form(mocker: MockerFixture) -> None:
    # given
    form_id = "test-form"
    user_id = UUID("11111111-1111-1111-1111-111111111111")
    organization_id = 1
    permissions = {"organization/1/algorithm": [AuthorizationVerb.CREATE]}
    translations = MagicMock(spec=NullTranslations)
    translations.gettext.return_value = "Translated Text"

    org_field = WebFormField(
        type=WebFormFieldType.SELECT,
        name="organization_id",
        label="Organization",
        options=[WebFormOption(value="1", display_value="Org 1")],
        default_value="1",
    )

    organizations_service = mocker.Mock(spec=OrganizationsService)
    mocker.patch("amt.api.forms.algorithm.get_organization_select_field", AsyncMock(return_value=org_field))

    # when
    result = await get_algorithm_form(
        form_id, translations, organizations_service, user_id, organization_id, permissions
    )

    # then
    assert isinstance(result, WebForm)
    assert result.id == form_id
    assert len(result.fields) == 1
    assert result.fields[0] == org_field


@pytest.mark.asyncio
async def test_get_algorithm_form_no_user_id(mocker: MockerFixture) -> None:
    # given
    form_id = "test-form"
    user_id: UUID | None = None
    organization_id = 1
    permissions = {"organization/1/algorithm": [AuthorizationVerb.CREATE]}
    translations = MagicMock(spec=NullTranslations)
    organizations_service = mocker.Mock(spec=OrganizationsService)

    # when/then
    with pytest.raises(ValueError, match="user_id is required"):
        await get_algorithm_form(form_id, translations, organizations_service, user_id, organization_id, permissions)


@pytest.mark.asyncio
async def test_get_algorithm_members_form(mocker: MockerFixture) -> None:
    # given
    form_id = "test-form"
    algorithm = Algorithm(id=123, name="Test Algorithm", organization_id=1)
    translations = MagicMock(spec=NullTranslations)
    translations.gettext.return_value = "Translated Text"

    # when
    result = await get_algorithm_members_form(form_id, translations, algorithm)

    # then
    assert isinstance(result, WebForm)
    assert result.id == form_id
    assert result.fields[0] is None
    assert result.fields[1] is None
    assert result.fields[2] is not None
    assert result.fields[2].name == "user_ids"
    assert result.fields[2].search_url == "/algorithm/123/users?returnType=search_select_field"  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
