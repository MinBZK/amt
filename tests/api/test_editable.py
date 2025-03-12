from typing import Any  # noqa: I001

import pytest
from pytest_mock import MockerFixture
from starlette.requests import Request

from amt.api.editable import get_enriched_resolved_editable, save_editable
from amt.api.editable_classes import Editable, EditModes, ResolvedEditable
from amt.api.editable_enforcers import EditableEnforcer
from amt.api.editable_validators import EditableValidatorMinMaxLength
from amt.api.editable_value_providers import EditableValuesProvider
from amt.schema.shared import IterableMeta
from amt.schema.webform import WebFormFieldImplementationType, WebFormOption
from amt.services.algorithms import AlgorithmsService
from tests.constants import default_auth_user, default_fastapi_request, default_algorithm_with_system_card

test_webform_options = [WebFormOption(value=option, display_value=option) for option in ["1", "2", "3"]]


class TestEnforcer(EditableEnforcer):
    async def enforce(self, **kwargs: Any) -> None:  # noqa: ANN401
        pass


class TestValuesProvider(EditableValuesProvider):
    async def get_values(self, request: Request) -> list[WebFormOption]:
        return test_webform_options


class TestEditables(metaclass=IterableMeta):
    ALGORITHM_EDITABLE_NAME: Editable = Editable(
        full_resource_path="algorithm/{algorithm_id}/name",
        implementation_type=WebFormFieldImplementationType.TEXT,
        validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
        enforcer=TestEnforcer(),
        values_provider=TestValuesProvider(),
    )
    ALGORITHM_PARENT: Editable = Editable(
        full_resource_path="algorithm/{algorithm_id}/parent",
        implementation_type=WebFormFieldImplementationType.PARENT,
        children=[
            ALGORITHM_EDITABLE_NAME,
            Editable(
                full_resource_path="algorithm/{algorithm_id}/lifecycle",
                implementation_type=WebFormFieldImplementationType.SELECT_LIFECYCLE,
            ),
        ],
    )
    ALGORITHM_EDITABLE_SYSTEMCARD_NAME = Editable(
        full_resource_path="algorithm/{algorithm_id}/system_card/name",
        implementation_type=WebFormFieldImplementationType.TEXT,
        validator=EditableValidatorMinMaxLength(min_length=3, max_length=100),
        values_provider=TestValuesProvider(),
    )
    ALGORITHM_EDITABLE_NAME.add_bidirectional_couple(ALGORITHM_EDITABLE_SYSTEMCARD_NAME)


@pytest.mark.asyncio
async def test_save_editable(mocker: MockerFixture):
    mocker.patch("amt.api.editable.editables", new=TestEditables())

    algorithms_service = mocker.Mock(spec=AlgorithmsService)
    algorithms_service.get.return_value = default_algorithm_with_system_card()

    context_variables: dict[str, Any] = {"algorithm_id": 1}
    full_resource_path = "algorithm/1/parent"
    algorithms_service = algorithms_service
    organizations_service = None
    user_id = default_auth_user()["sub"]

    editable: ResolvedEditable = await get_enriched_resolved_editable(
        context_variables=context_variables,
        full_resource_path=full_resource_path,
        algorithms_service=algorithms_service,
        organizations_service=None,
        edit_mode=EditModes.SAVE,
    )

    new_values = {
        "name": "new name",
        "lifecycle": "new lifecycle",
    }

    editable_context: dict[str, Any] = {
        "user_id": user_id,
        "new_values": new_values,
        "organizations_service": None,
        "algorithms_service": algorithms_service,
        "tasks_service": None,
    }

    saved_editable = await save_editable(editable, editable_context, True, algorithms_service, organizations_service)

    assert saved_editable is not None
    assert saved_editable.children[0].value == "new name"
    assert saved_editable.children[0].couples[0].value == "new name"
    assert saved_editable.children[1].value == "new lifecycle"


@pytest.mark.asyncio
async def test_get_enriched_resolved_editable(mocker: MockerFixture):
    mocker.patch("amt.api.editable.editables", new=TestEditables())

    algorithms_service = mocker.Mock(spec=AlgorithmsService)

    context_variables: dict[str, Any] = {"algorithm_id": 1}
    full_resource_path = "algorithm/1/parent"
    edit_mode = EditModes.EDIT
    algorithms_service = algorithms_service
    organizations_service = None
    user_id = default_auth_user()["sub"]
    request = default_fastapi_request()

    result = await get_enriched_resolved_editable(
        context_variables, full_resource_path, edit_mode, algorithms_service, organizations_service, user_id, request
    )

    assert result.children[0].form_options == test_webform_options
    assert result.children[1] is not None
    assert result.children[1].form_options is not None
    assert len(result.children[1].form_options) == 9
