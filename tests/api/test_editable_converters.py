from unittest.mock import AsyncMock

import pytest
from amt.api import editable_converters
from amt.api.lifecycles import Lifecycles
from amt.models import Organization


@pytest.mark.asyncio
async def test_editable_converter():
    editable_converter = editable_converters.EditableConverter()
    assert await editable_converter.read(in_value="test") == "test"
    assert await editable_converter.write(in_value="test") == "test"
    assert await editable_converter.read(in_value="test") == "test"


@pytest.mark.asyncio
async def test_editable_converter_for_organization_in_algorithm():
    editable_converter = editable_converters.EditableConverterForOrganizationInAlgorithm()
    organization: Organization = Organization(id=1, name="test organization name")

    mock_organization_service = AsyncMock()
    mock_organization_service.find_by_id_and_user_id.return_value = organization
    context = {"organizations_service": mock_organization_service, "user_id": 1}

    assert await editable_converter.read(in_value=organization) == 1
    assert await editable_converter.write(in_value="1", **context) == organization
    assert await editable_converter.view(in_value=organization) == "test organization name"


@pytest.mark.asyncio
async def test_editable_status_converter_for_systemcard():
    editable_converter = editable_converters.StatusConverterForSystemcard()
    assert (
        await editable_converter.read(in_value="Organisatieverantwoordelijkheden")
        == Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES.value
    )
    assert (
        await editable_converter.write(in_value=Lifecycles.ORGANIZATIONAL_RESPONSIBILITIES.value)
        == "Organisatieverantwoordelijkheden"
    )
    assert (
        await editable_converter.view(in_value="Dataverkenning en datapreparatie") == "Dataverkenning en datapreparatie"
    )
