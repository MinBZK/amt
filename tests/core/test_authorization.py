import pytest
from amt.core.authorization import get_user
from pytest_mock import MockerFixture


@pytest.mark.asyncio
def test_get_user(mocker: MockerFixture) -> None:
    mock_request = mocker.Mock(scope=["session"])
    mock_request.session = {"user": {"name": "user"}}
    mock_get_requested_language = mocker.patch("amt.core.authorization.get_requested_language", return_value="nl")
    user = get_user(mock_request)
    assert user == {"name": "user", "locale": "nl"}
    mock_get_requested_language.assert_called_once_with(mock_request)
