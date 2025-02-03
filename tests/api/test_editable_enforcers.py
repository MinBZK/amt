from unittest.mock import AsyncMock

import pytest
from amt.api.editable_enforcers import EditableEnforcerForOrganizationInAlgorithm
from amt.core.exceptions import AMTAuthorizationError
from amt.models import Organization


@pytest.mark.asyncio
async def test_editable_enforcer_for_organization_in_algorithm():
    editable_enforcer = EditableEnforcerForOrganizationInAlgorithm()
    organization: Organization = Organization(id=1, name="test organization name")

    mock_organization_service = AsyncMock()
    mock_organization_service.find_by_id_and_user_id.return_value = organization
    context = {"organizations_service": mock_organization_service, "user_id": 1, "new_values": {"organization": 2}}
    try:
        await editable_enforcer.enforce(**context)
    except AMTAuthorizationError:
        pytest.fail("Unexpected exception raised")

    mock_organization_service.find_by_id_and_user_id.side_effect = AMTAuthorizationError
    with pytest.raises(AMTAuthorizationError):
        await editable_enforcer.enforce(**context)
